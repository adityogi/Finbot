from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
import pandas as pd
import data_csv as db
import uuid
from datetime import datetime


# Flask App Configuration
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'financial_health_secret_key'

# Defaults
DEFAULTS = {
    "region_code": 'IN',
    "savings_rate": 20,
    "max_loan_to_income": 40,
}


# ---------- Helper Functions ----------
def calculate_score(analysis, country_data):
    targets = country_data.get('financial_targets', {})
    target_savings = targets.get('recommended_savings_rate', DEFAULTS["savings_rate"])
    max_loan_income = targets.get('max_loan_to_income', DEFAULTS["max_loan_to_income"])

    econ_data = country_data["economic_data"]
    monthly_avg_income = econ_data["average_income"] / 12

    score = 10

    # Income score
    income = analysis['monthly_income']
    if income < monthly_avg_income * 0.3: score -= 3
    elif income < monthly_avg_income * 0.5: score -= 2
    elif income < monthly_avg_income * 0.75: score -= 1
    elif income > monthly_avg_income: score += 1

    # Emergency fund
    if analysis['emergency_fund'] == 'no':
        score -= 2

    # Investments
    if analysis['funds_invested'] == 'no':
        score -= 1.5

    # Loan risks
    if analysis["loan_to_income_ratio"] > max_loan_income: score -= 2
    elif analysis["loan_to_income_ratio"] > max_loan_income * 0.75: score -= 1
    if analysis["loan_to_savings_ratio"] > 60: score -= 2
    elif analysis["loan_to_savings_ratio"] > 40: score -= 1

    # Expenditure variance
    if analysis["variance_percentage"] > 40: score -= 2
    elif analysis["variance_percentage"] > 20: score -= 1

    # Savings %
    if analysis["savings_percentage"] < target_savings * 0.75: score -= 1
    elif analysis["savings_percentage"] < target_savings: score -= 2

    return max(0, min(10, round(score, 1)))


def compute_financial_metrics(form_data):
    income = form_data['monthly_income']
    savings_pct = form_data['savings_percentage']

    monthly_savings = income * (savings_pct / 100)
    monthly_expenditure = income - monthly_savings
    lowest_savings_pct = ((monthly_savings - form_data['monthly_variance']) * 100 / income)

    # Ratios
    loan_to_income = (form_data['monthly_loan_payment'] / income * 100) if form_data['monthly_loan_payment'] else 0
    loan_to_savings = (form_data['outstanding_loan'] / monthly_savings) if monthly_savings and form_data['outstanding_loan'] else 0
    variance_pct = (form_data['monthly_variance'] / monthly_expenditure * 100) if monthly_expenditure else 0

    return {
        "monthly_savings": monthly_savings,
        "monthly_expenditure": monthly_expenditure,
        "lowest_savings_percentage": lowest_savings_pct,
        "loan_to_income_ratio": loan_to_income,
        "loan_to_savings_ratio": loan_to_savings,
        "variance_percentage": variance_pct,
    }


def sort_assessments(assessments, sort_by):
    if sort_by == 'date-asc':
        return sorted(assessments, key=lambda x: x['date'])
    elif sort_by == 'score-high':
        return sorted(assessments, key=lambda x: x['score'], reverse=True)
    elif sort_by == 'score-low':
        return sorted(assessments, key=lambda x: x['score'])
    # default: date-desc
    return sorted(assessments, key=lambda x: x['date'], reverse=True)


# ---------- Routes ----------
@app.route('/', methods=['GET', 'POST'])
def financial_health():
    if request.method == 'POST':
        region_code = DEFAULTS["region_code"]

        form_data = {
            'monthly_income': float(request.form['monthly_income']),
            'savings_percentage': float(request.form['savings_percentage']),
            'emergency_fund': request.form['emergency_fund'],
            'funds_invested': request.form['funds_invested'],
            'investment_type': request.form.get('investment_type', 'None'),
            'expected_return': float(request.form['expected_return']),
            'monthly_variance': float(request.form['monthly_variance']),
            'has_loans': request.form['has_loans'],
            'monthly_loan_payment': float(request.form.get('monthly_loan_payment', 0) or 0),
            'outstanding_loan': float(request.form.get('outstanding_loan', 0) or 0),
            'region_code': region_code,
        }

        country_data = db.get_country_data(region_code)
        form_data['currency'] = country_data["currency"]

        # Compute metrics
        metrics = compute_financial_metrics(form_data)

        # Session/user handling
        username = session.get('username', f"user_{uuid.uuid4().hex[:8]}")
        session['username'] = username
        user_id = db.get_or_create_user(username)

        # Build analysis dictionary
        analysis = {**form_data, **metrics, "economic_data": country_data.get('economic_data', {})}
        analysis["score"] = calculate_score(analysis, country_data)
        analysis["id"] = db.save_assessment(user_id, form_data, analysis["score"])

        return render_template('result.html', analysis=analysis, country_data=country_data)

    return render_template('form.html')


@app.route('/history')
def history():
    username = session.get('username')
    if not username:
        return redirect(url_for('financial_health'))

    user_id = db.get_or_create_user(username)
    assessments = db.get_user_assessments(user_id)

    # Standardize date
    for a in assessments:
        if isinstance(a['date'], str):
            a['date'] = datetime.strptime(a['date'], '%Y-%m-%d %H:%M:%S')
        country_data = db.get_country_data(a.get('region_code', 'IN'))
        a['region_name'] = country_data['name'] if country_data else 'India'
        a.setdefault('currency', {'symbol': '₹', 'code': 'INR', 'exchange_rate': 1})

    assessments = sort_assessments(assessments, request.args.get('sort', 'date-desc'))

    # Group by month-year
    assessments_by_month = {}
    for a in assessments:
        month_year = a['date'].strftime('%B %Y')
        assessments_by_month.setdefault(month_year, []).append(a)

    years = sorted({a['date'].year for a in assessments}, reverse=True)

    return render_template(
        'history.html',
        assessments=assessments,
        assessments_by_month=assessments_by_month,
        assessment_years=years,
        assessment_dates=[a['date'].strftime('%d %b %Y') for a in assessments],
        assessment_scores=[a['score'] for a in assessments],
    )


@app.route('/assessment/<int:assessment_id>')
def view_assessment(assessment_id):
    assessment = db.get_assessment_details(assessment_id)
    if not assessment:
        return redirect(url_for('history'))

    country_data = db.get_country_data(assessment["region_code"])
    assessment['currency'] = country_data["currency"]

    return render_template('result.html', analysis=assessment, country_data=country_data)


@app.route('/export/history')
def export_history():
    username = session.get('username')
    if not username:
        return redirect(url_for('financial_health'))

    user_id = db.get_or_create_user(username)
    assessments = db.get_user_assessments(user_id)

    export_data = []
    for a in assessments:
        date = a['date']
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        export_data.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Score': a['score'],
            'Monthly Income': a['monthly_income'],
            'Savings %': a['savings_percentage'],
            'Region': a.get('region_code', 'IN'),
            'Emergency Fund': a['emergency_fund'],
            'Invested': a['funds_invested']
        })

    df = pd.DataFrame(export_data)
    filename = f"financial_history_{username}.csv"
    df.to_csv(filename, index=False)

    return send_file(filename, as_attachment=True, download_name=filename,
                     mimetype='text/csv')
