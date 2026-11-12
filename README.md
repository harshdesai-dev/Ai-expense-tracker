# AI Expense Tracker

A beginner-friendly personal expense tracker with one AI feature: **Gemini analyzes category totals and gives practical spending observations and saving suggestions**.

## Features
- Record expenses with amount, category and date
- View total recorded spending
- View spending totals by category
- Delete an expense
- Generate AI spending insights with Gemini

## Run locally
1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Create and activate a virtual environment (optional but recommended):
   - Windows: `py -m venv venv` then `venv\Scripts\activate`
   - macOS/Linux: `python3 -m venv venv` then `source venv/bin/activate`
4. Install packages: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and paste your Gemini API key.
6. Start: `python app.py`
7. Open `http://127.0.0.1:5000`.

The SQLite database `expenses.db` is created automatically. Keep `.env` private; never upload your API key to GitHub.
