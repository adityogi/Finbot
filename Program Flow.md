
## Program Flow Chart Description

Below is a description of the flow for the Financial Health Assessment application for user visualization:

1. **User Accesses Form (`/`)**
   - Inputs financial data including income, savings, investment, loans, and expenditure variance.

2. **Submit Form (POST)**
   - Data is collected and validated.
   - Country-specific economic and financial targets are fetched from `regions.json`.

3. **Financial Calculations**
   - Monthly savings and expenditures computed.
   - Loan-to-income and loan-to-savings ratios calculated.
   - Expenditure variance percentage determined.

4. **Score Calculation**
   - Factors including income relative to average, emergency fund, investments, loans, variance, and savings percentage weighted.
   - Final score capped between 0 and 10.

5. **Save Assessment**
   - User identified via session or created.
   - Assessment data saved in CSV storage.

6. **Render Results Page (`/result.html`)**
   - Shows score, economic context, recommendations, and detailed metrics.

7. **History and Reports**
   - Users can view previous assessments on `/history`.
   - Sort/filter options available.
   - Export individual reports or full history in CSV format.
   - View detailed assessment reports at `/assessment/`.

***