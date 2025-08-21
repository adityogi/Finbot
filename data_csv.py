import csv
import os
import json
from datetime import datetime
from schema import TABLE_SCHEMAS

# --- Files and Schemas ---
USERS_FILE, ASSESSMENTS_FILE = "users.csv", "assessments.csv"
FILES = {
    USERS_FILE: TABLE_SCHEMAS["users"],
    ASSESSMENTS_FILE: TABLE_SCHEMAS["assessments"],
}


# ---------- CSV Utility ----------
def init_csv(file):
    """Ensure CSV file exists with headers."""
    if not os.path.exists(file):
        with open(file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FILES[file].keys())
            writer.writeheader()


def read_csv(file):
    schema = FILES[file]
    with open(file, newline="") as f:
        rows, out = list(csv.DictReader(f)), []
        for row in rows:
            converted = {}
            for k, v in row.items():
                typ = schema[k]
                if v == "":
                    converted[k] = 0 if typ == int else 0.0 if typ == float else ""
                else:
                    try:
                        converted[k] = typ(v)
                    except Exception:
                        converted[k] = v
            out.append(converted)
        return out


def write_csv(file, rows):
    cols = FILES[file].keys()
    with open(file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows({k: str(r.get(k, "")) for k in cols} for r in rows)


def append_csv(file, row):
    cols = FILES[file].keys()
    with open(file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writerow({k: str(row.get(k, "")) for k in cols})


def get_next_id(file):
    rows = read_csv(file)
    return max((int(r["id"]) for r in rows), default=0) + 1


# ---------- INIT ----------
def init():
    for file in FILES:
        init_csv(file)
    print("CSV storage initialized ✔")


# ---------- USERS ----------
def get_or_create_user(username):
    users = read_csv(USERS_FILE)
    user = next((u for u in users if u["username"] == username), None)
    if user:
        return int(user["id"])

    user_id = get_next_id(USERS_FILE)
    append_csv(USERS_FILE, {
        "id": user_id,
        "username": username,
        "created_at": datetime.now().isoformat(sep=" ", timespec="seconds"),
    })
    return user_id


# ---------- ASSESSMENTS ----------
def save_assessment(user_id, data, score):
    aid = get_next_id(ASSESSMENTS_FILE)
    append_csv(ASSESSMENTS_FILE, {
        "id": aid,
        "user_id": user_id,
        "date": datetime.now().isoformat(sep=" ", timespec="seconds"),
        **data,
        "score": score,
        "region_code": data.get("region_code", "IN"),
        "currency_data": data.get("currency_data", ""),
    })
    return aid


def get_user_assessments(user_id):
    return [r for r in read_csv(ASSESSMENTS_FILE) if int(r["user_id"]) == user_id]


def get_assessment_details(assessment_id):
    a = next((r for r in read_csv(ASSESSMENTS_FILE) if int(r["id"]) == assessment_id), None)
    if not a:
        return None

    monthly_income = a["monthly_income"]
    monthly_savings = a["savings_percentage"] * monthly_income / 100
    monthly_expenditure = monthly_income - monthly_savings

    a.update({
        "monthly_savings": monthly_savings,
        "monthly_expenditure": monthly_expenditure,
        "lowest_savings_percentage": 100 * (monthly_savings - a["monthly_variance"]) / monthly_income if a["monthly_variance"] else 0,
        "loan_to_income_ratio": (a["monthly_loan_payment"] / monthly_income) * 100 if monthly_income else 0,
        "variance_percentage": (a["monthly_variance"] / monthly_expenditure) * 100 if monthly_expenditure else 0,
    })

    print(f"Assessment: {a}")
    return a


# ---------- REGION DATA ----------
def load_region_data():
    try:
        with open("regions.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠ Error loading 'regions.json'")
        return {"countries": []}


def get_country_data(code):
    regions = load_region_data().get("countries", [])
    return next((c for c in regions if c.get("code") == code), 
                next((c for c in regions if c.get("code") == "IN"), None))
