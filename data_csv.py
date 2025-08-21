import csv
import os
import json
from datetime import datetime
from schema import TABLE_SCHEMAS

# CSV file names (1 CSV file per table)
USERS_FILE = 'users.csv'
ASSESSMENTS_FILE = 'assessments.csv'

FILE_TO_SCHEMA = {
    USERS_FILE: TABLE_SCHEMAS["users"],
    ASSESSMENTS_FILE: TABLE_SCHEMAS["assessments"],
}

# CSV schema definitions
USERS_COLUMNS = list(TABLE_SCHEMAS["users"].keys())
ASSESSMENTS_COLUMNS = list(TABLE_SCHEMAS["assessments"].keys())

# ---------- CSV Utility Functions ----------
def init_csv_file(file, columns):
    """Ensure CSV file exists with headers."""
    if not os.path.exists(file):
        with open(file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()

def read_csv(file):
    schema = FILE_TO_SCHEMA[file]
    with open(file, newline='') as f:
        rows = list(csv.DictReader(f))
        converted = []
        for row in rows:
            converted_row = {}
            for k, v in row.items():
                typ = schema[k]
                if v == '':
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
    with open(file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            out_row = {k: str(row[k]) if row[k] is not None else '' for k in columns}
            writer.writerow(out_row)

def append_csv(file, row, columns):
    with open(file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        out_row = {k: str(row[k]) if row[k] is not None else '' for k in columns}
        writer.writerow(out_row)

def get_next_id(file):
    rows = read_csv(file)
    if rows:
        return max(int(r["id"]) for r in rows) + 1
    return 1

# ---------- INIT FUNCTION ----------
def init():
    init_csv_file(USERS_FILE, USERS_COLUMNS)
    init_csv_file(ASSESSMENTS_FILE, ASSESSMENTS_COLUMNS)
    print("CSV storage system initialized successfully")

# ---------- USER FUNCTIONS ----------
def get_or_create_user(username):
    rows = read_csv(USERS_FILE)
    for r in rows:
        if r["username"] == username:
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
        "monthly_income": data.get("monthly_income"),
        "savings_percentage": data.get("savings_percentage"),
        "emergency_fund": data.get("emergency_fund"),
        "funds_invested": data.get("funds_invested"),
        "investment_type": data.get("investment_type"),
        "expected_return": data.get("expected_return"),
        "monthly_variance": data.get("monthly_variance"),
        "has_loans": data.get("has_loans"),
        "monthly_loan_payment": data.get("monthly_loan_payment", 0),
        "outstanding_loan": data.get("outstanding_loan", 0),
        "score": score,
        "region_code": "IN",
        "currency_data": ""
    }, ASSESSMENTS_COLUMNS)

    return assessment_id

# ---------- REGION DATA ----------
def load_region_data():
    try:
        with open('regions.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error loading region data. Ensure 'regions.json' exists and is valid.")
        return None

def get_country_data(country_code):
    regions = load_region_data()
    for c in regions.get("countries", []):
        if c.get("code") == country_code:
            return c
    # default
    for c in regions.get("countries", []):
        if c.get("code") == "IN":
            return c
    return None

# ---------- FETCH FUNCTIONS ----------
def get_user_assessments(user_id):
    rows = read_csv(ASSESSMENTS_FILE)
    return [r for r in rows if int(r["user_id"]) == user_id]

def get_assessment_details(assessment_id):
    assessments = read_csv(ASSESSMENTS_FILE)
    assessment = next((r for r in assessments if int(r["id"]) == assessment_id), None)
    if not assessment:
        return None

    monthly_savings = assessment["savings_percentage"] * assessment["monthly_income"] / 100
    assessment["monthly_savings"] = monthly_savings
    assessment["monthly_expenditure"] = assessment["monthly_income"] - monthly_savings
    variance = assessment["monthly_variance"]
    if assessment["monthly_variance"] < 0:
        variance = 0
    assessment['lowest_savings_percentage'] = 100 * (monthly_savings - variance) / assessment["monthly_income"]

    assessment["loan_to_income_ratio"] = (assessment['monthly_loan_payment'] / assessment["monthly_income"]) * 100
    assessment["variance_percentage"] = (assessment['monthly_variance'] / assessment["monthly_expenditure"]) * 100

    print(f"Assessment: {assessment}")
    return assessment

# ---------- RUN INIT ----------
if __name__ == "__main__":
    init()
