# coParentExpenses

# SharedCare Ledger

SharedCare Ledger is a co-parenting shared expenses site built in Python with Streamlit.

## Purpose

This project is designed to help co-parents:

- track shared child-related expenses
- upload and store receipts with each expense
- mark expenses as paid, partially paid, or outstanding
- maintain a clear shared balance

## Current Features

- professional homepage
- overview of core platform features
- placeholder summary for total, reimbursed, and outstanding expenses

## Tech Stack

- Python
- Streamlit

## Installation

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd coParentExpenses


   app.py
Your homepage / landing page.

pages/1_Add_Expense.py
Form to add an expense and upload a receipt.

pages/2_Ledger.py
Table of all expenses with payment status and outstanding amount.

pages/3_Summary.py
Dashboard totals: total spent, reimbursed, outstanding, who owes whom.

utils/db.py
Database connection and helper functions.

utils/models.py
Expense-related save/load/update functions.

utils/calculations.py
Balance math and summary logic.

init_db.py
Creates the database and tables the first time.

uploads/receipts/
Stores uploaded receipt files.