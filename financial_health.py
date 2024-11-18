from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def financial_health():
    if request.method == 'POST':
        # Get form data
        monthly_income = float(request.form['monthly_income'])
        savings_percentage = float(request.form['savings_percentage'])
        emergency_fund = request.form['emergency_fund']
        funds_invested = request.form['funds_invested']
        investment_type = request.form.get('investment_type', 'None')
        expected_return = float(request.form['expected_return'])
        monthly_variance = float(request.form['monthly_variance'])
        has_loans = request.form['has_loans']
        if request.form['monthly_loan_payment']:
            monthly_loan_payment = float(request.form.get('monthly_loan_payment', 0))
        else:
            monthly_loan_payment = 0
        if request.form.get('outstanding_loan'):
            outstanding_loan = float(request.form.get('outstanding_loan', 0))
        else:
            outstanding_loan = 0

        # Calculate metrics
        monthly_savings = monthly_income * (savings_percentage / 100)
        monthly_expenditure = monthly_income - monthly_savings
        loan_to_income_ratio = (monthly_loan_payment / monthly_income) * 100 if monthly_loan_payment > 0 else 0
        loan_to_savings_ratio = outstanding_loan / monthly_savings if monthly_savings > 0 else 0
        variance_percentage = (monthly_variance / monthly_expenditure) * 100 if monthly_expenditure > 0 else 0

        # Calculate score (0-10)
        score = 10  # Start with perfect score and deduct based on factors

        # Emergency fund check
        if emergency_fund == 'no':
            score -= 2

        # Investment check
        if funds_invested == 'no':
            score -= 1.5
        
        # Loan burden check
        if loan_to_income_ratio > 40:
            score -= 2
        elif loan_to_income_ratio > 30:
            score -= 1

        if loan_to_savings_ratio > 60:
            score -= 2

        # Expenditure variance check
        if variance_percentage > 20:
            score -= 1.5

        # Savings check
        if savings_percentage < 20:
            score -= 1

        # Ensure score stays within 0-10 range
        score = max(0, min(10, score))

        # Prepare analysis results
        analysis = {
            'monthly_savings': monthly_savings,
            'monthly_expenditure': monthly_expenditure,
            'loan_to_income_ratio': loan_to_income_ratio,
            'variance_percentage': variance_percentage,
            'score': round(score, 1)
        }
        if monthly_loan_payment > 0:
            analysis['monthly_loan_payment'] = monthly_loan_payment

        return render_template('result_wo_chart.html', analysis=analysis)

    return render_template('form.html')

@app.route('/login')
def wlcomePage():
    abc = dict()
    abc['a'] = 'apple'
    if abc.get('c'):
        print(abc['c'])
    else:
        print('not found')
    return "<html><h1>You are at my page</h1></html>"

if __name__ == '__main__':
    app.run(debug=True)
