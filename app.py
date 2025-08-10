from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
import pandas as pd
import data_csv as db
import uuid
from datetime import datetime

print (f"flask app name is {__name__}")
app = Flask(__name__,
            template_folder='templates',  # This should be the path to your templates
            static_folder='static')       # This should be the path to your static files
# app.secret_key = 'financial_health_secret_key'  # Required for session

# Application routes
@app.route('/', methods=['GET', 'POST'])
def financial_health():
    if request.method == 'POST':
        # Get form data
        form_data = {
            'monthly_income': float(request.form['monthly_income']),
            'savings_percentage': float(request.form['savings_percentage']),
            'emergency_fund': request.form['emergency_fund'],
            'funds_invested': request.form['funds_invested'],
            'investment_type': request.form.get('investment_type', 'None'),
            'expected_return': float(request.form['expected_return']),
            'monthly_variance': float(request.form['monthly_variance']),
            'has_loans': request.form['has_loans'],
            'monthly_loan_payment': float(request.form.get('monthly_loan_payment', 0)) if request.form.get('monthly_loan_payment') else 0,
            'outstanding_loan': float(request.form.get('outstanding_loan', 0)) if request.form.get('outstanding_loan') else 0,
            'region_code': 'IN',
        }

        # Get form data including region
        region_code = request.form.get('region', 'IN')
        country_data = db.get_country_data(region_code)
        # Store the currency data
        form_data['currency'] = country_data["currency"]

        # Calculate metrics (use local currency for UI but INR for calculations if needed)
        monthly_income = form_data['monthly_income']
        savings_percentage = form_data['savings_percentage']
        monthly_savings = monthly_income * (savings_percentage / 100)
        lowest_savings_percentage = (monthly_savings - form_data['monthly_variance']) * 100 / monthly_income
        monthly_savings = monthly_income * (savings_percentage / 100)
        monthly_expenditure = monthly_income - monthly_savings

        # Calculate loan-to-income ratio
        if form_data['monthly_loan_payment'] > 0:
            loan_to_income_ratio = (form_data['monthly_loan_payment'] / monthly_income) * 100
            monthly_expenditure = monthly_expenditure - form_data['monthly_loan_payment']
        else:
            loan_to_income_ratio = 0

        # Calculate loan-to-savings ratio
        if monthly_savings > 0:
            loan_to_savings_ratio = form_data['outstanding_loan'] / monthly_savings if form_data['outstanding_loan'] else 0
        else:
            loan_to_savings_ratio = 0

        # Calculate variance percentage
        if monthly_expenditure > 0:
            variance_percentage = (form_data['monthly_variance'] / monthly_expenditure) * 100
        else:
            variance_percentage = 0

        # Calculate score (0-10) - adjust based on country if needed
        score = 10  # Start with perfect score and deduct based on factors

        # Get country-specific targets if available
        target_savings_rate = country_data.get('financial_targets', {}).get('recommended_savings_rate', 20)
        max_loan_to_income = country_data.get('financial_targets', {}).get('max_loan_to_income', 40)

        # Emergency fund check
        if form_data['emergency_fund'] == 'no':
            score -= 2

        # Investment check
        if form_data['funds_invested'] == 'no':
            score -= 1.5

        # Loan burden check - use country-specific max if available
        if loan_to_income_ratio > max_loan_to_income:
            score -= 2
        elif loan_to_income_ratio > max_loan_to_income * 0.75:  # 75% of max
            score -= 1

        if loan_to_savings_ratio > 60:
            score -= 2

        # Expenditure variance check
        if variance_percentage > 20:
            score -= 1.5

        # Savings check - use country-specific target if available
        if savings_percentage < target_savings_rate:
            score -= 1

        # Ensure score stays within 0-10 range
        score = max(0, min(10, round(score, 1)))

        # Generate username from session or create a temporary one
        username = session.get('username', f"user_{uuid.uuid4().hex[:8]}")
        session['username'] = username
        user_id = db.get_or_create_user(username)

        # Save assessment to database
        assessment_id = db.save_assessment(user_id, form_data, score)

        # Prepare analysis results
        analysis = {
            'id': assessment_id,
            'monthly_income': monthly_income,
            'lowest_savings_percentage': lowest_savings_percentage,
            'savings_percentage': savings_percentage,
            'emergency_fund': form_data['emergency_fund'],
            'funds_invested': form_data['funds_invested'],
            'investment_type': form_data['investment_type'],
            'expected_return': form_data['expected_return'],
            'monthly_savings': monthly_savings,
            'monthly_expenditure': monthly_expenditure,
            'monthly_variance': form_data['monthly_variance'],
            'has_loans': form_data['has_loans'],
            'loan_to_income_ratio': loan_to_income_ratio,
            'variance_percentage': variance_percentage,
            'score': score,
            'region_code': region_code,
            'currency': form_data['currency'],
            'economic_data': country_data.get('economic_data', {})
        }

        if form_data['monthly_loan_payment'] > 0:
            analysis['monthly_loan_payment'] = form_data['monthly_loan_payment']
            analysis['outstanding_loan'] = form_data['outstanding_loan']

        return render_template('result.html', analysis=analysis,
                             country_data=country_data)

    return render_template('form.html')

@app.route('/history')
def history():
    username = session.get('username')
    if not username:
        return redirect(url_for('financial_health'))

    user_id = db.get_or_create_user(username)

    # Get filter parameters
    year_filter = request.args.get('year', 'all')
    sort_by = request.args.get('sort', 'date-desc')

    # Get assessments
    assessments = db.get_user_assessments(user_id)

    # Apply year filter if needed
    if year_filter != 'all':
        assessments = [a for a in assessments if str(datetime.strptime(a['date'], '%Y-%m-%d %H:%M:%S').year) == year_filter]

    # Apply sorting
    if sort_by == 'date-asc':
        assessments.sort(key=lambda x: x['date'])
    elif sort_by == 'score-high':
        assessments.sort(key=lambda x: x['score'], reverse=True)
    elif sort_by == 'score-low':
        assessments.sort(key=lambda x: x['score'])
    else:  # default: date-desc
        assessments.sort(key=lambda x: x['date'], reverse=True)

    # Process assessments for display
    for assessment in assessments:
        # Convert date string to datetime object
        if isinstance(assessment['date'], str):
            assessment['date'] = datetime.strptime(assessment['date'], '%Y-%m-%d %H:%M:%S')

        # Add region name
        region_code = assessment.get('region_code', 'IN')
        country_data = db.get_country_data(region_code)
        assessment['region_name'] = country_data['name'] if country_data else 'India'

        # Add currency info if missing
        if 'currency' not in assessment:
            assessment['currency'] = {
                'symbol': '₹',
                'code': 'INR',
                'exchange_rate': 1
            }

    # Group assessments by month and year
    assessments_by_month = {}
    for assessment in assessments:
        month_year = assessment['date'].strftime('%B %Y')
        if month_year not in assessments_by_month:
            assessments_by_month[month_year] = []
        assessments_by_month[month_year].append(assessment)

    # Get all years for filter dropdown
    assessment_years = sorted(list(set(a['date'].year for a in assessments)), reverse=True)

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
        # goals=goals
    )

@app.route('/assessment/<int:assessment_id>')
def view_assessment(assessment_id):
    assessment = db.get_assessment_details(assessment_id)
    if not assessment:
        return redirect(url_for('history'))

    country_data = db.get_country_data(assessment["region_code"])
    print(country_data)
    # Store the currency data
    assessment['currency'] = {
        'code': 'INR',
        'symbol': '₹',
        'exchange_rate': 1
    }
    return render_template('result.html',
                          analysis=assessment,
                          country_data=country_data)

@app.route('/export/<format>/<int:assessment_id>')
def export_report(format, assessment_id):
    print(f"Exporting {format} report for assessment {assessment_id}")

    if format == 'csv':
        csv_filename = generate_excel(assessment_id, "csv")
        if csv_filename and os.path.exists(csv_filename):
            return send_file(
                csv_filename,
                as_attachment=True,
                download_name=f"financial_report_{assessment_id}.csv",
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )


    return redirect(url_for('view_assessment', assessment_id=assessment_id))


@app.route('/export/history')
def export_history():
    username = session.get('username')
    if not username:
        return redirect(url_for('financial_health'))

    user_id = db.get_or_create_user(username)
    assessments = db.get_user_assessments(user_id)

    # Create DataFrame for export
    data = []
    for a in assessments:
        date = a['date']
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

        data.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Score': a['score'],
            'Monthly Income': a['monthly_income'],
            'Savings %': a['savings_percentage'],
            'Region': a.get('region_code', 'IN'),
            'Emergency Fund': a['emergency_fund'],
            'Invested': a['funds_invested']
        })

    df = pd.DataFrame(data)

    # Generate CSV file
    csv_filename = f"financial_history_{username}.csv"
    df.to_csv(csv_filename, index=False)
    

    return send_file(
        csv_filename,
        as_attachment=True,
        download_name=csv_filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


def generate_recommendations_text(assessment_id):
    """
    Generate personalized financial recommendations text based on user's financial analysis and country data.
    
    Args:
        country_data (dict): Contains country-specific financial and economic data
        analysis (dict): Contains user's financial analysis results
    
    Returns:
        str: Formatted text with personalized financial recommendations
    """
    country_data = db.get_country_data('IN')

    assessment = db.get_assessment_details(assessment_id)
    if not assessment:
        return None

    monthly_income = assessment.get('monthly_income', 0)
    savings_percentage = assessment.get('savings_percentage', 0)    
    monthly_savings = monthly_income * (savings_percentage / 100)
    monthly_expenditure = monthly_income - monthly_savings
    
    analysis = {
            'id': assessment_id,
            'monthly_income': monthly_income,
            'savings_percentage': savings_percentage,
            'emergency_fund': assessment.get('emergency_fund', 'no'),
            'funds_invested': assessment.get('funds_invested', 'no'),
            'investment_type': assessment.get('investment_type', 'none'),
            'expected_return': assessment.get('expected_return', 0),
            'monthly_savings': monthly_savings,
            'monthly_expenditure': monthly_expenditure,
            'monthly_variance': assessment.get('monthly_variance', 0),
            'has_loans': assessment.get('has_loans', 'no'),
            'variance_percentage': assessment.get('variance_percentage', 0),
            'score': assessment.get('score', 0),
            'region_code': 'IN',
            'currency': 'INR',
            'economic_data': country_data.get('economic_data', {})
        }

    if assessment.get('has_loans') == 'yes':
        monthly_loan_payment = assessment.get('monthly_loan_payment', 0)
        if monthly_loan_payment > 0:
            analysis['monthly_loan_payment'] = monthly_loan_payment
            analysis['outstanding_loan'] = assessment.get('outstanding_loan', 0)
            analysis['loan_to_income_ratio'] = (monthly_loan_payment / monthly_income * 100) 
        else:
            analysis['outstanding_loan'] = 0
            analysis['monthly_loan_payment'] = 0
    
    # Economic Context
    recommendations_text = f"ECONOMIC CONTEXT FOR {country_data['name'].upper()}\n"
    recommendations_text += f"- Current inflation rate is {country_data['economic_data']['inflation_rate']}%, which means your savings need to grow by at least this rate to maintain purchasing power.\n"
    
    income_comparison = "above" if analysis['monthly_income'] * 12 > country_data['economic_data']['average_income'] else "below"
    recommendations_text += f"- Average income in {country_data['name']} is Rs.{country_data['economic_data']['average_income']}. Your income is {income_comparison} the national average.\n\n"
    
    # Priority Actions
    recommendations_text += "PRIORITY ACTIONS"
    
    recommendations = []
    
    # Emergency Fund Check
    if analysis.get('emergency_fund') == "no":
        recommendations.append({
            'priority': 'High',
            'title': 'Build Emergency Fund',
            'description': f"In {country_data['name']}, experts recommend keeping {country_data['financial_targets']['emergency_fund_months']} months of expenses in an easily accessible emergency fund.",
            'action': f"Set aside a small amount each month specifically for emergencies until you reach {int(analysis['monthly_expenditure'] * country_data['financial_targets']['emergency_fund_months'])} INR."
        })
    
    # Savings Rate Check
    if analysis.get('savings_percentage') < country_data['financial_targets']['recommended_savings_rate']:
        recommendations.append({
            'priority': 'High',
            'title': 'Increase Savings Rate',
            'description': f"Your current savings rate ({analysis['savings_percentage']}%) is below the recommended {country_data['financial_targets']['recommended_savings_rate']}% for {country_data['name']}.",
            'action': f"Identify areas to reduce spending. Consider automating savings to reach at least {int(analysis['monthly_income'] * country_data['financial_targets']['recommended_savings_rate'] / 100)} INR per month."
        })
    
    # Debt Burden Check
    if analysis.get('has_loans') == "yes" and analysis.get('loan_to_income_ratio') > country_data['financial_targets']['max_loan_to_income']:
        recommendations.append({
            'priority': 'High',
            'title': 'Reduce Debt Burden',
            'description': f"Your loan-to-income ratio ({round(analysis['loan_to_income_ratio'], 1)}%) exceeds the recommended maximum of {country_data['financial_targets']['max_loan_to_income']}% for {country_data['name']}.",
            'action': "Consider debt consolidation or refinancing. Focus on paying off high-interest debt first while maintaining minimum payments on other debts."
        })
    
    # Investment Check
    if analysis.get('funds_invested') == "no" and analysis.get('monthly_savings') > 0:
        recommendations.append({
            'priority': 'Medium',
            'title': 'Start Investing',
            'description': f"With inflation at {country_data['economic_data']['inflation_rate']}% in {country_data['name']}, your uninvested savings are losing purchasing power.",
            'action': "Consider investing in low-cost index funds or speaking with a financial advisor about options suitable for your risk tolerance."
        })
    
    # Spending Variance Check
    if analysis.get('variance_percentage') > 20:
        recommendations.append({
            'priority': 'Medium',
            'title': 'Stabilize Monthly Spending',
            'description': f"Your spending varies significantly month-to-month ({round(analysis['variance_percentage'], 1)}% variance).",
            'action': "Create a detailed budget for essential expenses. Consider using the envelope method or a budgeting app to track spending in real-time."
        })
    
    # Investment Diversification Check
    if analysis.get('investment_type') == "none" and analysis.get('funds_invested') == "yes":
        recommendations.append({
            'priority': 'Low',
            'title': 'Diversify Investments',
            'description': "You've indicated you're investing but haven't specified an investment type.",
            'action': f"Consider a diversified portfolio appropriate for your age and risk tolerance. The current interest rate in {country_data['name']} is {country_data['economic_data']['interest_rate']}%."
        })
    
    # Display recommendations by priority
    for priority in ['High', 'Medium', 'Low']:
        priority_recommendations = [rec for rec in recommendations if rec['priority'] == priority]
        if priority_recommendations:
            recommendations_text += f"\n{priority.upper()} PRIORITY:\n"
            
            for rec in priority_recommendations:
                recommendations_text += f"* {rec['title']}\n"
                recommendations_text += f"  {rec['description']}\n"
                recommendations_text += f"  Action: {rec['action']}\n"
    
    # If no recommendations
    if not recommendations:
        recommendations_text += "\nYou're on the Right Track!\n"
        recommendations_text += "Your financial health appears to be good! Continue maintaining your current financial habits.\n"
        recommendations_text += "Action: Consider setting more ambitious financial goals or increasing your investments.\n"
    
    return recommendations_text

# Generate Excel report
def generate_excel(assessment_id, format="xlsx"):
    assessment = db.get_assessment_details(assessment_id)
    if not assessment:
        return None

    # Create DataFrame for assessment data
    monthly_savings = assessment['monthly_income'] * (assessment['savings_percentage'] / 100)
    monthly_expenditure = assessment['monthly_income'] - monthly_savings

    data = {
        'Metric': [
            'Date', 'Monthly Income', 'Savings Percentage', 'Monthly Savings',
            'Monthly Expenditure', 'Emergency Fund', 'Investments', 'Investment Type',
            'Expected Return', 'Has Loans', 'Monthly Loan Payment', 'Outstanding Loan',
            'Financial Health Score'
        ],
        'Value': [
            assessment['date'],
            f"₹{assessment['monthly_income']}",
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

    if format == "csv":
        # Save to CSV
        csv_filename = f"financial_report_{assessment_id}.csv"
        df.to_csv(csv_filename, index=False)

        return csv_filename
