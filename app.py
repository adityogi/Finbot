from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
import traceback
import pandas as pd
import data_csv as db
import uuid
from datetime import datetime
from jinja2 import ChoiceLoader, FileSystemLoader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Flask App Configuration
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)
app.secret_key = os.environ.get('SECRET_KEY', 'financial_health_secret_key')

# Configure multi-path template loader to support local and Vercel serverless environments
possible_template_dirs = [
    os.path.join(BASE_DIR, 'templates'),
    os.path.join(BASE_DIR, 'api', 'templates'),
    os.path.join(os.getcwd(), 'templates'),
    os.path.join(os.getcwd(), 'api', 'templates'),
    '/var/task/templates',
    '/var/task/api/templates',
]
valid_template_dirs = [d for d in possible_template_dirs if os.path.isdir(d)]
if valid_template_dirs:
    app.jinja_loader = ChoiceLoader([FileSystemLoader(d) for d in valid_template_dirs])

# Defaults
DEFAULTS = {
    "region_code": 'IN',
    "savings_rate": 20,
    "max_loan_to_income": 40,
}

# ---------- Error Handling ----------
@app.errorhandler(500)
@app.errorhandler(Exception)
def handle_error(error):
    tb = traceback.format_exc()
    app.logger.error(f"Application Error: {tb}")
    return f"""<!DOCTYPE html>
<html>
<head><title>Application Error</title></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 30px; background: #fff5f5; color: #333;">
    <div style="max-width: 800px; margin: 0 auto; background: #fff; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-left: 5px solid #e53e3e;">
        <h2 style="color: #e53e3e; margin-top: 0;">Application Error (500)</h2>
        <p><strong>Message:</strong> {error}</p>
        <pre style="background: #2d3748; color: #f7fafc; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 13px;">{tb}</pre>
        <p><a href="/" style="color: #3182ce;">Return to Home</a></p>
    </div>
</body>
</html>""", 500


# ---------- Helper Functions ----------
def calculate_score(analysis, country_data):
    targets = country_data.get('financial_targets', {}) if country_data else {}
    target_savings = targets.get('recommended_savings_rate', DEFAULTS["savings_rate"])
    max_loan_income = targets.get('max_loan_to_income', DEFAULTS["max_loan_to_income"])

    econ_data = country_data.get("economic_data", {}) if country_data else {}
    avg_income = econ_data.get("average_income", 174984)
    monthly_avg_income = avg_income / 12

    score = 10

    # Income score
    income = analysis.get('monthly_income', 0)
    if income < monthly_avg_income * 0.3: score -= 3
    elif income < monthly_avg_income * 0.5: score -= 2
    elif income < monthly_avg_income * 0.75: score -= 1
    elif income > monthly_avg_income: score += 1

    # Emergency fund
    if analysis.get('emergency_fund') == 'no':
        score -= 2

    # Investments
    if analysis.get('funds_invested') == 'no':
        score -= 1.5

    # Loan risks
    loan_to_income = analysis.get("loan_to_income_ratio", 0)
    if loan_to_income > max_loan_income: score -= 2
    elif loan_to_income > max_loan_income * 0.75: score -= 1

    loan_to_savings = analysis.get("loan_to_savings_ratio", 0)
    if loan_to_savings > 60: score -= 2
    elif loan_to_savings > 40: score -= 1

    # Expenditure variance
    variance_pct = analysis.get("variance_percentage", 0)
    if variance_pct > 40: score -= 2
    elif variance_pct > 20: score -= 1

    # Savings %
    savings_pct = analysis.get("savings_percentage", 0)
    if savings_pct < target_savings * 0.75: score -= 1
    elif savings_pct < target_savings: score -= 2

    return max(0, min(10, round(score, 1)))


def compute_financial_metrics(form_data):
    income = form_data.get('monthly_income', 0.0)
    savings_pct = form_data.get('savings_percentage', 0.0)

    monthly_savings = income * (savings_pct / 100)
    monthly_expenditure = income - monthly_savings
    monthly_variance = form_data.get('monthly_variance', 0.0)
    lowest_savings_pct = ((monthly_savings - monthly_variance) * 100 / income) if income > 0 else 0.0

    # Ratios
    loan_payment = form_data.get('monthly_loan_payment', 0.0)
    loan_to_income = (loan_payment / income * 100) if income > 0 and loan_payment else 0.0
    outstanding_loan = form_data.get('outstanding_loan', 0.0)
    loan_to_savings = (outstanding_loan / monthly_savings) if monthly_savings > 0 and outstanding_loan else 0.0
    variance_pct = (monthly_variance / monthly_expenditure * 100) if monthly_expenditure > 0 else 0.0

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
        try:
            region_code = DEFAULTS["region_code"]

            try:
                monthly_income = float(request.form.get('monthly_income') or 0)
            except (ValueError, TypeError):
                monthly_income = 0.0

            try:
                savings_percentage = float(request.form.get('savings_percentage') or 0)
            except (ValueError, TypeError):
                savings_percentage = 0.0

            try:
                expected_return = float(request.form.get('expected_return') or 0)
            except (ValueError, TypeError):
                expected_return = 0.0

            try:
                monthly_variance = float(request.form.get('monthly_variance') or 0)
            except (ValueError, TypeError):
                monthly_variance = 0.0

            try:
                monthly_loan_payment = float(request.form.get('monthly_loan_payment') or 0)
            except (ValueError, TypeError):
                monthly_loan_payment = 0.0

            try:
                outstanding_loan = float(request.form.get('outstanding_loan') or 0)
            except (ValueError, TypeError):
                outstanding_loan = 0.0

            form_data = {
                'monthly_income': monthly_income,
                'savings_percentage': savings_percentage,
                'emergency_fund': request.form.get('emergency_fund', 'no'),
                'funds_invested': request.form.get('funds_invested', 'no'),
                'investment_type': request.form.get('investment_type', 'None'),
                'expected_return': expected_return,
                'monthly_variance': monthly_variance,
                'has_loans': request.form.get('has_loans', 'no'),
                'monthly_loan_payment': monthly_loan_payment,
                'outstanding_loan': outstanding_loan,
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
        except Exception as e:
            tb = traceback.format_exc()
            return f"<h1>Caught Exception: {type(e).__name__}</h1><pre>{tb}</pre>", 200

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
            try:
                a['date'] = datetime.strptime(a['date'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    a['date'] = datetime.fromisoformat(a['date'].replace(' ', 'T'))
                except ValueError:
                    a['date'] = datetime.now()
        country_data = db.get_country_data(a.get('region_code', 'IN'))
        a['region_name'] = country_data['name'] if country_data else 'India'
        a.setdefault('currency', {'symbol': '₹', 'code': 'INR', 'exchange_rate': 83.2})

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

    country_data = db.get_country_data(assessment.get("region_code", "IN"))
    assessment['currency'] = country_data["currency"]
    assessment['economic_data'] = country_data.get('economic_data', {})

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

@app.route('/export/history')
def export_history():
    username = session.get('username')
    if not username:
        return redirect(url_for('financial_health'))

    user_id = db.get_or_create_user(username)
    assessments = db.get_user_assessments(user_id)
    if not assessments:
        return redirect(url_for('history'))

    df = pd.DataFrame(assessments)
    filename = os.path.join(db.DATA_DIR, f"history_{user_id}.csv")
    df.to_csv(filename, index=False)

    return send_file(
        filename,
        as_attachment=True,
        download_name=f"financial_history_{datetime.now().strftime('%Y%m%d')}.csv"
    )

# Generate CSV report
def generate_csv(assessment_id):
    assessment = db.get_assessment_details(assessment_id)
    if not assessment:
        return None

    income = assessment.get('monthly_income', 0.0)
    savings_pct = assessment.get('savings_percentage', 0.0)
    monthly_savings = income * (savings_pct / 100)
    monthly_expenditure = income - monthly_savings

    data = {
        'Metric': [
            'Date', 'Monthly Income', 'Savings Percentage', 'Monthly Savings',
            'Monthly Expenditure', 'Emergency Fund', 'Investments', 
            'Investment Type','Expected Return', 'Has Loans', 
            'Monthly Loan Payment', 'Outstanding Loan', 'Financial Health Score'
        ],
        'Value': [
            assessment.get('date', ''),
            f"₹{income}",
            f"{savings_pct}%",
            f"₹{monthly_savings}",
            f"₹{monthly_expenditure}",
            assessment.get('emergency_fund', ''),
            assessment.get('funds_invested', ''),
            assessment.get('investment_type', ''),
            f"{assessment.get('expected_return', 0)}%",
            assessment.get('has_loans', ''),
            f"₹{assessment.get('monthly_loan_payment', 0)}",
            f"₹{assessment.get('outstanding_loan', 0)}",
            f"{assessment.get('score', 0)}/10"
        ]
    }

    df = pd.DataFrame(data)
    filename = os.path.join(db.DATA_DIR, f"financial_report_{assessment_id}.csv")
    df.to_csv(filename, index=False)

    return filename

if __name__ == '__main__':
    db.init()
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
