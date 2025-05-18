# Financial Health Assessment Application

## Project Overview

The Financial Health Assessment Application is an interactive web-based tool that evaluates a user's financial health based on comprehensive analysis of income, savings, investments, budget breakdown, loans, and expenditure patterns. The application provides personalized recommendations based on regional economic factors and allows users to track their financial progress over time.

## Features

### A. Core Financial Assessment

1. **Comprehensive Financial Evaluation**
   - Analyzes income, savings rate, investments, loans, and spending patterns
   - Calculates a financial health score on a scale of 0-10
   - Provides customized recommendations based on identified financial weaknesses

2. **Regional Context Analysis**
   - Supports multiple countries/regions with appropriate currency conversion
   - Adjusts recommendations based on regional economic indicators
   - Provides comparative analysis against regional averages and benchmarks

3. **Multi-step Assessment Process**
   - User-friendly form with progressive disclosure of fields
   - Optional budget breakdown for detailed expenditure analysis
   - Validation to ensure accurate data entry

### B. Data Visualization Dashboard

1. **Interactive Charts**
   - Income allocation pie chart (savings vs. expenses)
   - Budget category breakdown bar chart
   - Financial health radar chart showing strengths/weaknesses
   - Historical score tracking line chart

2. **Metric Visualization**
   - Visual representation of key financial metrics
   - Color-coded indicators for areas of concern
   - Comparative visualizations against recommended values

### C. Financial Goal Setting & Tracking

1. **Goal Management**
   - Create and track multiple financial goals
   - Set target amounts and deadlines
   - Monitor progress with visual indicators
   - Adjust goals as financial circumstances change

2. **Goal Recommendations**
   - Suggestions for appropriate financial goals based on assessment
   - Templates for common financial objectives
   - Information on realistic timeframes for achievement

### D. Budget Category Breakdown

1. **Detailed Expense Tracking**
   - Eight standard budget categories (housing, transportation, food, etc.)
   - Percentage and amount analysis of spending patterns
   - Recommendations for budget optimization
   - Comparison to standard budgeting guidelines

### E. Export & Reporting

1. **PDF Reports**
   - Generate comprehensive financial health reports
   - Include visualizations and personalized recommendations
   - Professional formatting for printing or sharing

2. **Excel Exports**
   - Detailed data export with all financial metrics
   - Multiple sheets for different aspects (assessment, budget, goals)
   - Raw data for further analysis in spreadsheet software

### F. History & Progress Tracking

1. **Assessment History**
   - Store and view past financial assessments
   - Organize by month and year with filtering capabilities
   - Track score improvements over time
   - Compare assessments to identify trends

## Technical Architecture

### Core Technologies

1. **Backend**
   - Python 3.x with Flask web framework
   - SQLite database for data persistence
   - Pandas for data manipulation and Excel export
   - FPDF for PDF report generation

2. **Frontend**
   - HTML5, CSS3 for structure and styling
   - JavaScript for interactive elements
   - Chart.js for data visualization
   - Font Awesome for icons and visual elements

### Key Components

1. **Flask Application**
   - Route handling for different application views
   - Form processing and validation
   - Database interaction through helper functions
   - Session management for user persistence

2. **Database**
   - User management with anonymous session-based identification
   - Assessment storage with comprehensive financial data
   - Goal tracking with progress metrics
   - Budget category breakdown storage

3. **Templates**
   - Jinja2 template engine for dynamic HTML rendering
   - Responsive design for various screen sizes
   - Modular components for consistent UI/UX

## Installation & Setup

### Prerequisites

1. **Python Environment**
   - Python 3.7 or higher
   - pip package manager
   - virtualenv (recommended for isolation)

2. **Required Libraries**
   - Flask for web application framework
   - Pandas for data processing
   - FPDF for PDF generation
   - SQLite3 (included in Python standard library)

### Installation Steps

1. **Clone or Download the Project**
   ```bash
   git clone https://github.com/yourusername/financial-health-assessment.git
   cd financial-health-assessment
   ```

2. **Create and Activate Virtual Environment (Optional but Recommended)**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install Required Packages**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the Database**
   ```bash
   python initialize_db.py
   # Or run the application which will initialize the DB automatically
   ```

5. **Create Regions Data File**
   - Create a file named `regions.json` in the project root directory
   - Use the provided example structure for regional data

### Running the Application

1. **Start the Flask Development Server**
   ```bash
   python financial_health.py
   ```

2. **Access the Application**
   - Open a web browser and navigate to http://127.0.0.1:5000
   - The application should load the financial assessment form

## Usage Guide

### Conducting a Financial Assessment

1. **Navigate to the Assessment Form**
   - Access the home page at http://127.0.0.1:5000
   - Select your region/country from the dropdown menu

2. **Complete the Basic Information**
   - Enter your monthly income
   - Specify your savings percentage
   - Provide information about emergency funds, investments, and loans
   - Click "Next" to proceed or "Skip to Calculate" if you don't want to enter budget details

3. **Enter Budget Breakdown (Optional)**
   - Provide expenditure amounts for different budget categories
   - Click "Calculate Financial Health" to process your assessment

4. **Review Your Results**
   - Examine your financial health score
   - Review detailed metrics and visualizations
   - Read personalized recommendations
   - Export reports if desired

### Managing Financial Goals

1. **Access the Goals Page**
   - Click on "Financial Goals" in the navigation menu

2. **Create a New Goal**
   - Enter goal name, target amount, and target date
   - Input current progress if applicable
   - Click "Add Goal" to save

3. **Track Goal Progress**
   - View all goals with progress bars
   - Update goals as you make progress
   - Review estimated completion timelines

### Viewing Assessment History

1. **Access the History Page**
   - Click on "History" in the navigation menu

2. **Filter and Sort History**
   - Use year filter to narrow down results
   - Sort by date or score
   - View assessments organized by month

3. **Analyze Progress**
   - Track score improvements over time
   - View detailed assessment information
   - Export history data for external analysis

## File Structure

```
financial-health-assessment/
├── financial_health.py      # Main application file
├── requirements.txt         # Package dependencies
├── regions.json             # Regional economic data
├── initialize_db.py         # Database initialization script
├── static/                  # Static assets
│   ├── css/                 # Stylesheets
│   ├── js/                  # JavaScript files
│   └── img/                 # Images and icons
└── templates/               # HTML templates
    ├── form.html            # Assessment form
    ├── result.html          # Results display
    ├── goals.html           # Goals management
    ├── history.html         # Assessment history
    ├── assessment_detail.html  # Individual assessment view
    └── pdf_report.html      # PDF report template
```

## Database Schema

### Users Table

| Column     | Type      | Description                      |
|------------|-----------|----------------------------------|
| id         | INTEGER   | Primary key                      |
| username   | TEXT      | Unique user identifier           |
| created_at | TIMESTAMP | Account creation timestamp       |

### Assessments Table

| Column             | Type      | Description                        |
|--------------------|-----------|------------------------------------|
| id                 | INTEGER   | Primary key                        |
| user_id            | INTEGER   | Foreign key to users table         |
| date               | TIMESTAMP | Assessment date                    |
| monthly_income     | REAL      | Monthly income amount              |
| savings_percentage | REAL      | Percentage of income saved         |
| emergency_fund     | TEXT      | Emergency fund status (yes/no)     |
| funds_invested     | TEXT      | Investment status (yes/no)         |
| investment_type    | TEXT      | Type of investments                |
| expected_return    | REAL      | Expected investment return rate    |
| monthly_variance   | REAL      | Monthly spending variance          |
| has_loans          | TEXT      | Loan status (yes/no)               |
| monthly_loan_payment | REAL    | Monthly loan payment amount        |
| outstanding_loan   | REAL      | Outstanding loan balance           |
| score              | REAL      | Financial health score (0-10)      |
| region_code        | TEXT      | Country/region code                |
| currency_data      | TEXT      | JSON string of currency information|

### Budget Categories Table

| Column         | Type      | Description                        |
|----------------|-----------|------------------------------------|
| id             | INTEGER   | Primary key                        |
| assessment_id  | INTEGER   | Foreign key to assessments table   |
| housing        | REAL      | Housing expenses                   |
| transportation | REAL      | Transportation expenses            |
| food           | REAL      | Food expenses                      |
| utilities      | REAL      | Utilities expenses                 |
| healthcare     | REAL      | Healthcare expenses                |
| entertainment  | REAL      | Entertainment expenses             |
| personal       | REAL      | Personal expenses                  |
| other          | REAL      | Other expenses                     |

### Goals Table

| Column         | Type      | Description                        |
|----------------|-----------|------------------------------------|
| id             | INTEGER   | Primary key                        |
| user_id        | INTEGER   | Foreign key to users table         |
| goal_name      | TEXT      | Name/description of goal           |
| goal_amount    | REAL      | Target amount                      |
| current_amount | REAL      | Current progress amount            |
| target_date    | TEXT      | Goal target date                   |
| created_at     | TIMESTAMP | Goal creation timestamp            |
| region_code    | TEXT      | Country/region code                |
| currency_symbol| TEXT      | Currency symbol for display        |

## Customization Options

### Adding New Regions

To add support for additional countries/regions:

1. Edit the `regions.json` file to include new country data:
   ```json
   {
     "name": "Country Name",
     "code": "COUNTRY_CODE",
     "currency": {
       "code": "CURRENCY_CODE",
       "symbol": "SYMBOL",
       "exchange_rate": RATE_TO_USD
     },
     "economic_data": {
       "inflation_rate": RATE,
       "average_income": AMOUNT,
       "interest_rate": RATE,
       "unemployment_rate": RATE
     },
     "financial_targets": {
       "emergency_fund_months": NUMBER,
       "recommended_savings_rate": PERCENTAGE,
       "max_loan_to_income": PERCENTAGE
     }
   }
   ```

2. Update the region selector in `form.html` to include the new option.

### Modifying Scoring Criteria

To customize how financial health is scored:

1. Edit the scoring logic in the `financial_health()` route in `financial_health.py`
2. Adjust the deduction values for different factors
3. Add or remove scoring criteria as needed

### Adding New Budget Categories

To include additional budget categories:

1. Modify the `budget_categories` table schema in `init_db()`
2. Update the budget section in `form.html`
3. Adjust the budget visualization in `result.html`

## Troubleshooting

### Common Issues

1. **Database Errors**
   - **Issue**: "Unable to open database file"
   - **Solution**: Ensure the application has write permissions in the directory

2. **PDF Generation Fails**
   - **Issue**: PDF export returns an error
   - **Solution**: Install FPDF using `pip install fpdf==1.7.2` and ensure all dependencies are met

3. **Template Not Found**
   - **Issue**: Jinja2 template errors
   - **Solution**: Verify the correct directory structure with templates in the `templates` folder

4. **Currency Conversion Issues**
   - **Issue**: Incorrect currency conversion
   - **Solution**: Update exchange rates in `regions.json` with current values

### Getting Help

For additional assistance:

1. Check the Flask documentation: https://flask.palletsprojects.com/
2. Review Chart.js documentation for visualization issues: https://www.chartjs.org/docs/
3. Submit issues on the project repository

## Future Enhancements

Planned features for future versions:

1. User authentication system with secure login
2. Automated financial data import from banking APIs
3. Machine learning-based recommendations
4. Mobile application version
5. Advanced retirement planning tools
6. Debt payoff strategy calculator
7. Investment portfolio analyzer

---

*This Financial Health Assessment Application was developed as an educational project to demonstrate web application development with Python and Flask while providing useful financial planning tools.*
