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

    assessments = sorted(assessments, key=lambda x: x['date'], reverse=True)

    # Group by month-year
    assessments_by_month = {}
    for a in assessments:
        month_year = a['date'].strftime('%B %Y')
        assessments_by_month.setdefault(month_year, []).append(a)

    assessment_years = sorted({a['date'].year for a in assessments}, reverse=True)
    # Get data for chart
    assessment_dates = [a['date'].strftime('%d %b %Y') for a in sorted(assessments, key=lambda x: x['date'])]
    assessment_scores = [a['score'] for a in sorted(assessments, key=lambda x: x['date'])]

    return render_template(
        'history.html',
        assessments=assessments,
        assessments_by_month=assessments_by_month,
        assessment_years=assessment_years,
        assessment_dates=assessment_dates,
        assessment_scores=assessment_scores,
    )

@app.route('/assessment/<int:assessment_id>')
def view_assessment(assessment_id):
    assessment = db.get_assessment_details(assessment_id)
    if not assessment:
        return redirect(url_for('history'))

    country_data = db.get_country_data(assessment["region_code"])
    assessment['currency'] = country_data["currency"]

    return render_template('result.html', analysis=assessment, country_data=country_data)

@app.route('/export/csv/<int:assessment_id>')
def export_report(assessment_id):
    filename = generate_csv(assessment_id)
    if filename and os.path.exists(filename):
        return send_file(
            filename,
            as_attachment=True,
            download_name=f"financial_report_{assessment_id}.csv"
        )

    return redirect(url_for('view_assessment', assessment_id=assessment_id))

# Generate CSV report
def generate_csv(assessment_id):
    assessment = db.get_assessment_details(assessment_id)
    if not assessment:
        return None

    income = assessment['monthly_income']
    monthly_savings = income * (assessment['savings_percentage'] / 100)
    monthly_expenditure = income - monthly_savings

    data = {
        'Metric': [
            'Date', 'Monthly Income', 'Savings Percentage', 'Monthly Savings',
            'Monthly Expenditure', 'Emergency Fund', 'Investments', 
            'Investment Type','Expected Return', 'Has Loans', 
            'Monthly Loan Payment', 'Outstanding Loan', 'Financial Health Score'
        ],
        'Value': [
            assessment['date'],
            f"₹{income}",
            f"{assessment['savings_percentage']}%",
            f"₹{monthly_savings}",
            f"₹{monthly_expenditure}",
            assessment['emergency_fund'],
            assessment['funds_invested'],
            assessment['investment_type'],
            f"{assessment['expected_return']}%",
            assessment['has_loans'],
            f"₹{assessment.get('monthly_loan_payment', 0)}",
            f"₹{assessment.get('outstanding_loan', 0)}",
            f"{assessment['score']}/10"
        ]
    }

    df = pd.DataFrame(data)
    filename = f"financial_report_{assessment_id}.csv"
    df.to_csv(filename, index=False)

    return filename
