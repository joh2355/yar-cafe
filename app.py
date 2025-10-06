from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from werkzeug.security import check_password_hash
import mysql.connector
import os
#asfasdfasf
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super_secret_key")

# -------------------
# Database Connection
# -------------------
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "cafe_app")
    )

# -------------------
# Auth Helpers
# -------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("⚠️ Please log in first", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("🚫 Admin access only", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return wrapper

# -------------------
# Login / Logout
# -------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash(f"✅ Welcome {username}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("❌ Invalid username or password", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("👋 Logged out", "info")
    return redirect(url_for("login"))

# -------------------
# Dashboard
# -------------------
@app.route("/")
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT IFNULL(SUM(amount),0) AS total FROM investments")
    total_investments = cursor.fetchone()["total"]

    cursor.execute("SELECT IFNULL(SUM(amount),0) AS total FROM expenses")
    total_expenses = cursor.fetchone()["total"]

    cursor.execute("SELECT IFNULL(SUM(total),0) AS total FROM orders")
    total_sales = cursor.fetchone()["total"]

    balance = total_investments + total_sales - total_expenses

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        balance=balance,
        role=session.get("role"),
        username=session.get("username")
    )

# -------------------
# Inventory (Admin only)
# -------------------
@app.route("/inventory")
@login_required
@admin_required
def inventory():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM menu_items ORDER BY category, name")
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("inventory.html", items=items, role=session.get("role"))

@app.route("/inventory/add", methods=["POST"])
@login_required
@admin_required
def inventory_add():
    name = request.form["name"]
    price = float(request.form["price"])
    stock = int(request.form["stock"])
    category = request.form.get("category", "")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO menu_items (name, price, stock, category) VALUES (%s, %s, %s, %s)",
        (name, price, stock, category),
    )
    conn.commit()
    cursor.close()
    conn.close()

    flash("✅ Inventory item added!", "success")
    return redirect(url_for("inventory"))

@app.route("/inventory/edit/<int:item_id>", methods=["GET", "POST"])
@login_required
@admin_required
def inventory_edit(item_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form["name"]
        price = float(request.form["price"])
        stock = int(request.form["stock"])
        category = request.form["category"]

        cursor.execute(
            "UPDATE menu_items SET name=%s, price=%s, stock=%s, category=%s WHERE id=%s",
            (name, price, stock, category, item_id),
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("✏️ Inventory item updated!", "info")
        return redirect(url_for("inventory"))

    cursor.execute("SELECT * FROM menu_items WHERE id=%s", (item_id,))
    item = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template("inventory_edit.html", item=item, role=session.get("role"))

@app.route("/inventory/delete/<int:item_id>", methods=["POST"])
@login_required
@admin_required
def inventory_delete(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM menu_items WHERE id=%s", (item_id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash("🗑️ Inventory item deleted!", "warning")
    return redirect(url_for("inventory"))

# -------------------
# Menu Management (Admin only)
# -------------------
@app.route("/menu")
@login_required
@admin_required
def menu_manage():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM menu ORDER BY category, name")
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("menu_manage.html", items=items, role=session.get("role"))

@app.route("/menu/add", methods=["POST"])
@login_required
@admin_required
def menu_add():
    name = request.form["name"]
    price = float(request.form["price"])
    category = request.form["category"]
    emoji = request.form.get("emoji", "")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO menu (name, category, price, emoji) VALUES (%s, %s, %s, %s)",
        (name, category, price, emoji),
    )
    conn.commit()
    cursor.close()
    conn.close()

    flash("✅ Menu item added!", "success")
    return redirect(url_for("menu_manage"))

@app.route("/menu/edit/<int:item_id>", methods=["GET", "POST"])
@login_required
@admin_required
def menu_edit(item_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form["name"]
        price = float(request.form["price"])
        category = request.form["category"]
        emoji = request.form.get("emoji", "")

        cursor.execute(
            "UPDATE menu SET name=%s, category=%s, price=%s, emoji=%s WHERE id=%s",
            (name, category, price, emoji, item_id),
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("✏️ Menu item updated!", "info")
        return redirect(url_for("menu_manage"))

    cursor.execute("SELECT * FROM menu WHERE id=%s", (item_id,))
    item = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template("menu_edit.html", item=item)

@app.route("/menu/delete/<int:item_id>")
@login_required
@admin_required
def menu_delete(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM menu WHERE id=%s", (item_id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash("🗑️ Menu item deleted!", "warning")
    return redirect(url_for("menu_manage"))

# -------------------
# Expenses (Admin only)
# -------------------
@app.route("/expenses")
@login_required
@admin_required
def expenses():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM expenses ORDER BY expense_date DESC")
    expenses = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("expenses.html", expenses=expenses, role=session.get("role"))

@app.route("/expenses/add", methods=["POST"])
@login_required
@admin_required
def expenses_add():
    description = request.form["description"]
    amount = float(request.form["amount"])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (description, amount) VALUES (%s, %s)",
        (description, amount),
    )
    conn.commit()
    cursor.close()
    conn.close()

    flash("✅ Expense added!", "success")
    return redirect(url_for("expenses"))

# -------------------
# Investments (Admin only)
# -------------------
@app.route("/investments")
@login_required
@admin_required
def investments():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM investments ORDER BY investment_date DESC")
    investments = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("investments.html", investments=investments, role=session.get("role"))

@app.route("/investments/add", methods=["POST"])
@login_required
@admin_required
def investments_add():
    description = request.form["description"]
    amount = float(request.form["amount"])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO investments (description, amount) VALUES (%s, %s)",
        (description, amount),
    )
    conn.commit()
    cursor.close()
    conn.close()

    flash("✅ Investment added!", "success")
    return redirect(url_for("investments"))

# -------------------
# Orders (All users)
# -------------------
@app.route("/orders")
@login_required
def orders():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders ORDER BY order_date DESC")
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("orders.html", orders=orders, role=session.get("role"))

@app.route("/orders/new", methods=["GET", "POST"])
@login_required
def new_order():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        cursor.execute("SELECT * FROM menu")
        items = cursor.fetchall()
        total = 0
        order_items = []

        for it in items:
            qty = int(request.form.get(f"qty_{it['id']}", 0))
            if qty > 0:
                subtotal = qty * float(it["price"])
                total += subtotal
                order_items.append((it["id"], qty, it["price"]))

        if total > 0:
            cursor.execute(
                "INSERT INTO orders (total, payment_method) VALUES (%s, %s)",
                (total, request.form["payment_method"]),
            )
            order_id = cursor.lastrowid

            for item_id, qty, price in order_items:
                cursor.execute(
                    "INSERT INTO order_items (order_id, item_id, quantity, price) VALUES (%s, %s, %s, %s)",
                    (order_id, item_id, qty, price),
                )

            conn.commit()
            return redirect(url_for("receipt", order_id=order_id))

    cursor.execute("SELECT * FROM menu ORDER BY category, name")
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("new_order.html", items=items, role=session.get("role"))

@app.route("/receipt/<int:order_id>")
@login_required
def receipt(order_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM orders WHERE id=%s", (order_id,))
    order = cursor.fetchone()

    cursor.execute("""
        SELECT oi.quantity, oi.price, m.name, m.category, m.emoji
        FROM order_items oi 
        JOIN menu m ON oi.item_id = m.id 
        WHERE oi.order_id=%s
    """, (order_id,))
    items = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("receipt.html", order=order, items=items, role=session.get("role"))

# -------------------
# Reports (Admin only)
# -------------------
@app.route("/report")
@login_required
@admin_required
def report():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT IFNULL(SUM(amount),0) AS total FROM expenses")
    expenses = float(cursor.fetchone()["total"] or 0)

    cursor.execute("SELECT IFNULL(SUM(amount),0) AS total FROM investments")
    investments = float(cursor.fetchone()["total"] or 0)

    cursor.execute("SELECT IFNULL(SUM(total),0) AS total FROM orders")
    sales = float(cursor.fetchone()["total"] or 0)

    balance = investments + sales - expenses

    cursor.close()
    conn.close()

    return render_template(
        "report.html",
        expenses=expenses,
        investments=investments,
        sales=sales,
        balance=balance,
        role=session.get("role")
    )

# -------------------
# Run App
# -------------------
if __name__ == "__main__":
    print("🚀 Starting Café App...")
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
