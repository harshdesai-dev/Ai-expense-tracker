
import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)

secret_key = os.getenv("FLASK_SECRET_KEY")
if not secret_key:
    raise RuntimeError("FLASK_SECRET_KEY is missing.")

app.secret_key = secret_key


def ask_gemini(prompt):
    key = os.getenv("GEMINI_API_KEY")

    if not key:
        raise ValueError("Gemini API key is not configured.")

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/"
        f"models/{model}:generateContent"
    )

    response = requests.post(
        url,
        params={"key": key},
        json={
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        },
        timeout=25
    )

    response.raise_for_status()

    data = response.json()
    candidates = data.get("candidates", [])

    if not candidates:
        raise ValueError("Gemini returned no analysis.")

    parts = candidates[0].get("content", {}).get("parts", [])

    if not parts or not parts[0].get("text"):
        raise ValueError("Gemini returned an empty response.")

    return parts[0]["text"].strip()


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/ai-insights")
def ai_insights():
    data = request.get_json(silent=True) or {}
    expenses = data.get("expenses")

    if not isinstance(expenses, list) or not expenses:
        return jsonify(error="Add at least one expense first."), 400

    if len(expenses) > 500:
        return jsonify(error="Too many expenses to analyze at once."), 400

    category_totals = {}
    total = 0.0

    try:
        for expense in expenses:
            if not isinstance(expense, dict):
                return jsonify(error="Invalid expense data."), 400

            category = str(expense.get("category", "Other")).strip()
            amount = expense.get("amount")

            if (
                not category
                or len(category) > 50
                or isinstance(amount, bool)
                or not isinstance(amount, (int, float))
                or not 0 < amount < 100000000
            ):
                return jsonify(error="Invalid expense data."), 400

            total += amount
            category_totals[category] = (
                category_totals.get(category, 0) + amount
            )

        if not category_totals or total <= 0:
            return jsonify(error="No valid expenses found."), 400

        summary = ", ".join(
            f"{category}: ₹{amount:.2f}"
            for category, amount in sorted(
                category_totals.items(),
                key=lambda item: item[1],
                reverse=True
            )
        )

        prompt = (
            "You are a practical personal budgeting assistant. "
            "Analyze these expense totals. "
            "Give 3 concise observations and 2 realistic saving "
            "suggestions. Do not shame the user. "
            f"Total recorded spending: ₹{total:.2f}. "
            f"Category totals: {summary}"
        )

        result = ask_gemini(prompt)

        return jsonify(insights=result)

    except requests.RequestException:
        app.logger.exception("Gemini API request failed")
        return jsonify(error="Could not connect to Gemini. Try again."), 502

    except (ValueError, KeyError, TypeError):
        app.logger.exception("Gemini response processing failed")
        return jsonify(error="Could not generate AI insights."), 502


if __name__ == "__main__":
    app.run(debug=False)
