import sqlite3

# Database setup
DB_NAME = 'financial_health.db'

def init_db():
    """Initialize the database schema or update it if it already exists"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Users table
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Check if assessments table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assessments'")
    table_exists = c.fetchone() is not None

    if not table_exists:
        # Create assessments table with all columns including new ones
        c.execute('''
        CREATE TABLE assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            monthly_income REAL,
            savings_percentage REAL,
            emergency_fund TEXT,
            funds_invested TEXT,
            investment_type TEXT,
            expected_return REAL,
            monthly_variance REAL,
            has_loans TEXT,
            monthly_loan_payment REAL,
            outstanding_loan REAL,
            score REAL,
            region_code TEXT DEFAULT 'IN',
            currency_data TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
    else:
        # Check if region_code column exists
        try:
            c.execute("SELECT region_code FROM assessments LIMIT 1")
        except sqlite3.OperationalError:
            # Add region_code column if it doesn't exist
            c.execute("ALTER TABLE assessments ADD COLUMN region_code TEXT DEFAULT 'IN'")

        # Check if currency_data column exists
        try:
            c.execute("SELECT currency_data FROM assessments LIMIT 1")
        except sqlite3.OperationalError:
            # Add currency_data column if it doesn't exist
            c.execute("ALTER TABLE assessments ADD COLUMN currency_data TEXT")

    # Budget categories table
    c.execute('''
    CREATE TABLE IF NOT EXISTS budget_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        assessment_id INTEGER,
        housing REAL,
        transportation REAL,
        food REAL,
        utilities REAL,
        healthcare REAL,
        entertainment REAL,
        personal REAL,
        other REAL,
        FOREIGN KEY (assessment_id) REFERENCES assessments (id)
    )
    ''')

    # Goals table - add region_code and currency_symbol fields
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='goals'")
    goals_exists = c.fetchone() is not None

    if not goals_exists:
        c.execute('''
        CREATE TABLE goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            goal_name TEXT,
            goal_amount REAL,
            current_amount REAL,
            target_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            region_code TEXT DEFAULT 'IN',
            currency_symbol TEXT DEFAULT '₹',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
    else:
        # Check if region_code column exists in goals table
        try:
            c.execute("SELECT region_code FROM goals LIMIT 1")
        except sqlite3.OperationalError:
            c.execute("ALTER TABLE goals ADD COLUMN region_code TEXT DEFAULT 'IN'")

        # Check if currency_symbol column exists in goals table
        try:
            c.execute("SELECT currency_symbol FROM goals LIMIT 1")
        except sqlite3.OperationalError:
            c.execute("ALTER TABLE goals ADD COLUMN currency_symbol TEXT DEFAULT '₹'")

    conn.commit()
    conn.close()

    print("Database initialized successfully")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Users table
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Assessments table
    c.execute('''
    CREATE TABLE IF NOT EXISTS assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        monthly_income REAL,
        savings_percentage REAL,
        emergency_fund TEXT,
        funds_invested TEXT,
        investment_type TEXT,
        expected_return REAL,
        monthly_variance REAL,
        has_loans TEXT,
        monthly_loan_payment REAL,
        outstanding_loan REAL,
        score REAL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Budget categories table
    c.execute('''
    CREATE TABLE IF NOT EXISTS budget_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        assessment_id INTEGER,
        housing REAL,
        transportation REAL,
        food REAL,
        utilities REAL,
        healthcare REAL,
        entertainment REAL,
        personal REAL,
        other REAL,
        FOREIGN KEY (assessment_id) REFERENCES assessments (id)
    )
    ''')

    # Goals table
    c.execute('''
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        goal_name TEXT,
        goal_amount REAL,
        current_amount REAL,
        target_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Helper functions for database operations
def get_or_create_user(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = c.fetchone()

    if user:
        user_id = user[0]
    else:
        c.execute("INSERT INTO users (username) VALUES (?)", (username,))
        conn.commit()
        user_id = c.lastrowid

    conn.close()
    return user_id

def save_assessment(user_id, data, score):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''
    INSERT INTO assessments (
        user_id, monthly_income, savings_percentage, emergency_fund,
        funds_invested, investment_type, expected_return, monthly_variance,
        has_loans, monthly_loan_payment, outstanding_loan, score
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, data['monthly_income'], data['savings_percentage'], data['emergency_fund'],
        data['funds_invested'], data['investment_type'], data['expected_return'], data['monthly_variance'],
        data['has_loans'], data.get('monthly_loan_payment', 0), data.get('outstanding_loan', 0), score
    ))

    assessment_id = c.lastrowid

    # Save budget categories if provided
    if 'budget_categories' in data:
        categories = data['budget_categories']
        c.execute('''
        INSERT INTO budget_categories (
            assessment_id, housing, transportation, food, utilities,
            healthcare, entertainment, personal, other
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            assessment_id, categories['housing'], categories['transportation'],
            categories['food'], categories['utilities'], categories['healthcare'],
            categories['entertainment'], categories['personal'], categories['other']
        ))

    conn.commit()
    conn.close()
    return assessment_id

def save_goal(user_id, goal_data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''
    INSERT INTO goals (user_id, goal_name, goal_amount, current_amount, target_date)
    VALUES (?, ?, ?, ?, ?)
    ''', (
        user_id, goal_data['goal_name'], goal_data['goal_amount'],
        goal_data.get('current_amount', 0), goal_data['target_date']
    ))

    goal_id = c.lastrowid
    conn.commit()
    conn.close()
    return goal_id

def get_user_goals(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('SELECT * FROM goals WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    goals = [dict(row) for row in c.fetchall()]

    conn.close()
    return goals

def load_region_data():
    """Load region data from JSON file"""
    try:
        with open('regions.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return default data if file is missing or invalid
        return {"countries": [
            {
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
        ]}

def get_country_data(country_code):
    """Get data for a specific country"""
    regions = load_region_data()
    for country in regions.get("countries", []):
        if country.get("code") == country_code:
            return country
    # Default to IN if country not found
    for country in regions.get("countries", []):
        if country.get("code") == "IN":
            return country
    return None

def get_user_assessments(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('SELECT * FROM assessments WHERE user_id = ? ORDER BY date DESC', (user_id,))
    assessments = [dict(row) for row in c.fetchall()]

    conn.close()
    return assessments

def get_assessment_details(assessment_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('SELECT * FROM assessments WHERE id = ?', (assessment_id,))
    assessment = c.fetchone()
    if not assessment:
        return None

    assessment_dict = dict(assessment)

    c.execute('SELECT * FROM budget_categories WHERE assessment_id = ?', (assessment_id,))
    budget = c.fetchone()
    if budget:
        assessment_dict['budget_categories'] = dict(budget)

    conn.close()
    return assessment_dict
