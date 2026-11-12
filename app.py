import os, sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv
import requests

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "local-development-key")
DB = os.path.join(os.path.dirname(__file__), "expenses.db")

def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            expense_date TEXT NOT NULL
        )""")

def ask_gemini(prompt):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("Add your Gemini API key to the .env file.")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    response = requests.post(url, params={"key": key},
        json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=25)
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

@app.route("/")
def index():
    with connect() as con:
        expenses = con.execute("SELECT * FROM expenses ORDER BY expense_date DESC, id DESC").fetchall()
        total = con.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0]
        categories = con.execute("SELECT category, SUM(amount) AS total FROM expenses GROUP BY category ORDER BY total DESC").fetchall()
    return render_template("index.html", expenses=expenses, total=total, categories=categories)

@app.post("/add")
def add():
    title=request.form.get("title","").strip()
    category=request.form.get("category","Other").strip()
    date=request.form.get("expense_date","").strip()
    try: amount=float(request.form.get("amount","0"))
    except ValueError: amount=0
    if title and date and amount > 0:
        with connect() as con:
            con.execute("INSERT INTO expenses(title,category,amount,expense_date) VALUES(?,?,?,?)",(title,category,amount,date))
    return redirect(url_for("index"))

@app.post("/delete/<int:expense_id>")
def delete(expense_id):
    with connect() as con: con.execute("DELETE FROM expenses WHERE id=?",(expense_id,))
    return redirect(url_for("index"))

@app.post("/ai-insights")
def ai_insights():
    with connect() as con:
        rows=con.execute("SELECT category, SUM(amount) AS total FROM expenses GROUP BY category ORDER BY total DESC").fetchall()
        total=con.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0]
    if not rows: return jsonify(error="Add at least one expense first."),400
    summary=", ".join(f"{r['category']}: ₹{r['total']:.2f}" for r in rows)
    try:
        result=ask_gemini(
            "You are a practical personal budgeting assistant. Analyze these expense totals. "
            "Give 3 concise observations and 2 realistic saving suggestions. Do not shame the user. "
            f"Total recorded spending: ₹{total:.2f}. Category totals: {summary}"
        )
        return jsonify(insights=result)
    except Exception as e:
        return jsonify(error=f"AI request failed: {e}"),502

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
