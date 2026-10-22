import csv
import os
import shutil
from datetime import datetime
from schema import TABLE_SCHEMAS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_data_dir():
    # If custom DATA_DIR is provided
    if os.environ.get('DATA_DIR'):
        target = os.environ.get('DATA_DIR')
        os.makedirs(target, exist_ok=True)
        return target

    # On Vercel / AWS Lambda, use /tmp which is writable
    if os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
        return '/tmp'

    # Check if BASE_DIR is writable
    try:
        test_file = os.path.join(BASE_DIR, '.writable_test')
        with open(test_file, 'w') as f:
            f.write('1')
        os.remove(test_file)
        return BASE_DIR
    except (OSError, IOError):
        return '/tmp'

DATA_DIR = get_data_dir()
USERS_FILE = os.path.join(DATA_DIR, 'users.csv')
ASSESSMENTS_FILE = os.path.join(DATA_DIR, 'assessments.csv')

# CSV schema definitions
USERS_COLUMNS = list(TABLE_SCHEMAS["users"].keys())
ASSESSMENTS_COLUMNS = list(TABLE_SCHEMAS["assessments"].keys())

def get_schema(file):
    base = os.path.basename(file)
    if 'user' in base:
        return TABLE_SCHEMAS["users"]
    elif 'assessment' in base:
        return TABLE_SCHEMAS["assessments"]
    return TABLE_SCHEMAS.get("assessments", {})

# ---------- CSV Utility Functions ----------
def init_csv_file(file, columns):
    """Ensure CSV file exists with headers."""
    os.makedirs(os.path.dirname(os.path.abspath(file)), exist_ok=True)
    if not os.path.exists(file):
        base_seed = os.path.join(BASE_DIR, os.path.basename(file))
        if os.path.exists(base_seed) and os.path.abspath(base_seed) != os.path.abspath(file):
            shutil.copyfile(base_seed, file)
        else:
            with open(file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()

def read_csv(file):
    init()
    schema = get_schema(file)
    with open(file, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
        converted = []
        for row in rows:
            converted_row = {}
            for k, v in row.items():
                typ = schema.get(k, str)
                if v == '' or v is None:
                    # Empty string handling
                    if typ == int or typ == float:
                        converted_row[k] = 0 if typ == int else 0.0
                    else:
                        converted_row[k] = ''
                else:
                    # Try conversion
                    try:
                        converted_row[k] = typ(v)
                    except Exception:
                        converted_row[k] = v  # Fallback: leave as-is
            converted.append(converted_row)
        return converted

def write_csv(file, rows, columns):
    init()
    with open(file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            out_row = {k: str(row.get(k, '')) if row.get(k) is not None else '' for k in columns}
            writer.writerow(out_row)

def append_csv(file, row, columns):
    init()
    with open(file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        out_row = {k: str(row.get(k, '')) if row.get(k) is not None else '' for k in columns}
        writer.writerow(out_row)

def get_next_id(file):
    rows = read_csv(file)
    if rows:
        return max(int(r.get("id", 0)) for r in rows) + 1
    return 1

# ---------- INIT FUNCTION ----------
def init():
    init_csv_file(USERS_FILE, USERS_COLUMNS)
    init_csv_file(ASSESSMENTS_FILE, ASSESSMENTS_COLUMNS)

# ---------- USER FUNCTIONS ----------
def get_or_create_user(username):
    rows = read_csv(USERS_FILE)
    for r in rows:
        if r.get("username") == username:
            return int(r["id"])
    # create new user
    user_id = get_next_id(USERS_FILE)
    append_csv(USERS_FILE, {
        "id": user_id,
        "username": username,
        "created_at": datetime.now().isoformat(sep=' ', timespec='seconds')
    }, USERS_COLUMNS)
    return user_id

# ---------- ASSESSMENT FUNCTIONS ----------
def save_assessment(user_id, data, score):
    assessment_id = get_next_id(ASSESSMENTS_FILE)
    
    append_csv(ASSESSMENTS_FILE, {
        "id": assessment_id,
        "user_id": user_id,
        "date": datetime.now().isoformat(sep=' ', timespec='seconds'),
        "monthly_income": data.get("monthly_income", 0.0),
        "savings_percentage": data.get("savings_percentage", 0.0),
        "emergency_fund": data.get("emergency_fund", "no"),
        "funds_invested": data.get("funds_invested", "no"),
        "investment_type": data.get("investment_type", "None"),
        "expected_return": data.get("expected_return", 0.0),
        "monthly_variance": data.get("monthly_variance", 0.0),
        "has_loans": data.get("has_loans", "no"),
        "monthly_loan_payment": data.get("monthly_loan_payment", 0.0),
        "outstanding_loan": data.get("outstanding_loan", 0.0),
        "score": score,
        "region_code": data.get("region_code", "IN"),
        "currency_data": ""
    }, ASSESSMENTS_COLUMNS)

    return assessment_id

# ---------- REGION DATA ----------

DEFAULT_COUNTRY = {
    "name": "India",
    "code": "IN",
    "currency": {
        "code": "INR",
        "symbol": "₹",
        "exchange_rate": 83.2
    },
    "economic_data": {
        "inflation_rate": 5.6,
        "average_income": 174984,
        "interest_rate": 6.5,
        "unemployment_rate": 7.1
    },
    "financial_targets": {
        "emergency_fund_months": 8,
        "recommended_savings_rate": 30,
        "max_loan_to_income": 40
    }
}

def get_country_data(country_code="IN"):
    regions = { 
        "countries": [
            DEFAULT_COUNTRY
        ] 
    }
    for c in regions.get("countries", []):
        if c.get("code") == country_code:
            return c
    return DEFAULT_COUNTRY

# ---------- FETCH FUNCTIONS ----------
def get_user_assessments(user_id):
    rows = read_csv(ASSESSMENTS_FILE)
    return [r for r in rows if int(r.get("user_id", -1)) == user_id]

def get_assessment_details(assessment_id):
    assessments = read_csv(ASSESSMENTS_FILE)
    assessment = next((r for r in assessments if int(r.get("id", -1)) == assessment_id), None)
    if not assessment:
        return None

    income = float(assessment.get("monthly_income") or 0.0)
    savings_pct = float(assessment.get("savings_percentage") or 0.0)
    savings = income * (savings_pct / 100)
    assessment["monthly_savings"] = savings
    expenditure = income - savings
    assessment["monthly_expenditure"] = expenditure
    variance = float(assessment.get("monthly_variance") or 0.0)
    if variance < 0:
        variance = 0.0
    assessment["lowest_savings_percentage"] = (100 * (savings - variance) / income) if income > 0 else 0.0
    loan_payment = float(assessment.get("monthly_loan_payment") or 0.0)
    assessment["loan_to_income_ratio"] = ((loan_payment / income) * 100) if income > 0 else 0.0
    assessment["variance_percentage"] = ((variance / expenditure) * 100) if expenditure > 0 else 0.0

    return assessment

# ---------- RUN INIT ----------
init()

if __name__ == "__main__":
    init()
    print("CSV storage system initialized successfully in:", DATA_DIR)
