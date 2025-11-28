from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from datetime import datetime
import numpy as np

app = Flask(__name__)
app.secret_key = 'ajmal-expensetrack-key'

# MySQL connection function
def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="ajmal203",  # Your MySQL password
        database="expenses_tracker"
    )
    return conn

# ------------------ Routes ------------------

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get all expenses
        cursor.execute('SELECT * FROM expenses ORDER BY date DESC')
        expenses = cursor.fetchall()

        # Get categories
        cursor.execute('SELECT DISTINCT category FROM expenses')
        categories = [row['category'] for row in cursor.fetchall()]

        # Get budget
        cursor.execute('SELECT * FROM budget LIMIT 1')
        budget_row = cursor.fetchone()
        budget = budget_row['budget'] if budget_row else 0

        # Total expenses & balance
        total_expenses = sum([exp['amount'] for exp in expenses])
        balance = budget - total_expenses

        # Category-wise expenses
        category_expenses = []
        for cat in categories:
            cursor.execute('SELECT SUM(amount) AS total FROM expenses WHERE category=%s', (cat,))
            result = cursor.fetchone()
            category_expenses.append(result['total'] if result['total'] else 0)

        # Monthly expenses
        monthly = {}
        for exp in expenses:
            month = datetime.strptime(str(exp['date']), '%Y-%m-%d').strftime('%B')
            monthly[month] = monthly.get(month, 0) + exp['amount']

        monthly_data = {'labels': list(monthly.keys()), 'values': list(monthly.values())}

        # Predict next month expense using mean
        future_prediction = np.mean(monthly_data['values']) if monthly_data['values'] else 0

        cursor.close()
        conn.close()

        return render_template(
            'index.html',
            expenses=expenses,
            categories=categories,
            total_expenses=total_expenses,
            balance=balance,
            budget=budget,
            category_expenses=category_expenses,
            monthly_expenses=monthly_data,
            future_expenses_prediction=future_prediction
        )

    except Exception as e:
        flash(f"Error loading page: {e}", "error")
        return render_template('index.html', 
            expenses=[],
            categories=[],
            total_expenses=0,
            balance=0,
            budget=0,
            category_expenses=[],
            monthly_expenses={'labels':[], 'values':[]},
            future_expenses_prediction=0
        )

# Add expense
@app.route('/add', methods=['POST'])
def add_expense():
    try:
        category = request.form['category']
        amount = float(request.form['amount'])
        description = request.form.get('description', '')
        date = request.form['date']
        datetime.strptime(date, '%Y-%m-%d')  # Validate date

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'INSERT INTO expenses (category, amount, description, date) VALUES (%s, %s, %s, %s)',
            (category, amount, description, date)
        )
        conn.commit()

        # Check if over budget
        cursor.execute('SELECT SUM(amount) AS total FROM expenses')
        total_spent = cursor.fetchone()['total'] or 0
        cursor.execute('SELECT * FROM budget LIMIT 1')
        budget_row = cursor.fetchone()
        if budget_row and total_spent > budget_row['budget']:
            flash(f"Warning: You have exceeded the budget by ₹{total_spent - budget_row['budget']}", "warning")
        else:
            flash("Expense added successfully!", "success")

        cursor.close()
        conn.close()
    except Exception as e:
        flash(f"Error adding expense: {e}", "error")

    return redirect(url_for('index'))

# Delete expense
@app.route('/delete/<int:id>')
def delete_expense(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM expenses WHERE id=%s', (id,))
        conn.commit()
        flash("Expense deleted", "success")
        cursor.close()
        conn.close()
    except Exception as e:
        flash(f"Error deleting expense: {e}", "error")
    return redirect(url_for('index'))

# Update budget
@app.route('/update_budget', methods=['POST'])
def update_budget():
    try:
        new_budget = float(request.form['budget'])
        if new_budget < 0:
            raise ValueError("Budget cannot be negative")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM budget LIMIT 1')
        existing = cursor.fetchone()
        if existing:
            cursor.execute('UPDATE budget SET budget=%s WHERE id=1', (new_budget,))
        else:
            cursor.execute('INSERT INTO budget (id, budget) VALUES (1, %s)', (new_budget,))
        conn.commit()
        flash("Budget updated successfully", "success")
        cursor.close()
        conn.close()
    except Exception as e:
        flash(f"Error updating budget: {e}", "error")

    return redirect(url_for('index'))

# ------------------ Run App ------------------
if __name__ == '__main__':
    app.run(debug=True)
