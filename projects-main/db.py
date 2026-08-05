import mysql.connector
from datetime import date, datetime


def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",        #
        database="moneywise"
    )

# ---------------- USER QUERIES ----------------

def get_user_by_email(email):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def create_user(first, last, email, otp):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (first_name, last_name, email, otp, is_verified) "
        "VALUES (%s,%s,%s,%s,0)",
        (first, last, email, otp)
    )
    conn.commit()
    cur.close()
    conn.close()

def update_otp(email, otp):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET otp=%s WHERE email=%s",
        (otp, email)
    )
    conn.commit()
    cur.close()
    conn.close()

def verify_user_otp(email, otp):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute(
        "SELECT otp FROM users WHERE email=%s",
        (email,)
    )
    user = cur.fetchone()

    if user and user["otp"] == otp:
        cur.execute(
            "UPDATE users SET otp=NULL WHERE email=%s",
            (email,)
        )
        conn.commit()
        result = True
    else:
        result = False

    cur.close()
    conn.close()
    return result


def set_user_password(email, hashed_password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET password=%s WHERE email=%s",
        (hashed_password, email)
    )
    conn.commit()
    cur.close()
    conn.close()

def insert_income(uid, source, amount, income_date, note):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO income (uid, source, amount, income_date, notes) "
        "VALUES (%s,%s,%s,%s,%s)",
        (uid, source, amount, income_date, note)
    )
    conn.commit()
    cur.close()
    conn.close()

def user_has_income(uid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM income WHERE uid=%s LIMIT 1",
        (uid,)
    )
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result is not None


# ---------- MONTHLY INCOME ----------
def get_monthly_income(uid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DATE_FORMAT(income_date,'%Y-%m'), SUM(amount)
        FROM income
        WHERE uid=%s
        GROUP BY 1
        ORDER BY 1
    """, (uid,))
    data = dict(cur.fetchall())
    cur.close()
    conn.close()
    return data

# ---------- MONTHLY EXPENSE ----------
def get_monthly_expense(uid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DATE_FORMAT(expense_date,'%Y-%m'), SUM(amount)
        FROM expenses
        WHERE uid=%s
        GROUP BY 1
        ORDER BY 1
    """, (uid,))
    data = dict(cur.fetchall())
    cur.close()
    conn.close()
    return data

# ---------- CURRENT MONTH TOTALS ----------
def get_current_month_totals(uid):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COALESCE(SUM(amount),0)
        FROM income
        WHERE uid=%s AND MONTH(income_date)=MONTH(CURDATE())
        AND YEAR(income_date)=YEAR(CURDATE())
    """, (uid,))
    income = cur.fetchone()[0]

    cur.execute("""
        SELECT COALESCE(SUM(amount),0)
        FROM expenses
        WHERE uid=%s AND MONTH(expense_date)=MONTH(CURDATE())
        AND YEAR(expense_date)=YEAR(CURDATE())
    """, (uid,))
    expense = cur.fetchone()[0]

    cur.close()
    conn.close()
    return income, expense

# ---------- TOP 3 EXPENSES ----------
def get_top_3_expenses(uid):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT expense_title, amount
        FROM expenses
        WHERE uid=%s
        AND MONTH(expense_date)=MONTH(CURDATE())
        AND YEAR(expense_date)=YEAR(CURDATE())
        ORDER BY amount DESC
        LIMIT 3
    """, (uid,))

    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def get_expense_by_category(uid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE uid=%s
        GROUP BY category
        ORDER BY SUM(amount) 
    """, (uid,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return rows

def get_expense_transactions(uid, start_date=None, end_date=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    query = """
        SELECT expense_id, expense_title, category, amount, expense_date, note AS notes
        FROM expenses
        WHERE uid=%s
    """
    params = [uid]
    if start_date and end_date:
        query += " AND expense_date BETWEEN %s AND %s"
        params.extend([start_date, end_date])

    cur.execute(query, tuple(params))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def insert_expense(uid, title, category, amount, date, notes):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO expenses
        (uid, expense_title, category, amount, expense_date, note)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (uid, title, category, amount, date, notes))
    conn.commit()
    cur.close()
    conn.close()







def get_assets(uid, start_date=None, end_date=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT 
            asset_id,
            asset_name,
            asset_type,
            category,
            amount,
            annual_return_percent as annual_return,
            purchase_date as asset_date
        FROM assets
        WHERE uid = %s
    """
    params = [uid]
    if start_date and end_date:
        query += " AND purchase_date BETWEEN %s AND %s"
        params.extend([start_date, end_date])
    query += " ORDER BY asset_date DESC"

    cur.execute(query, tuple(params))

    assets = cur.fetchall()
    cur.close()
    conn.close()

    today = date.today()

    for a in assets:
        # ----- FIX 1: handle asset_date -----
        asset_date = a["asset_date"]
        if isinstance(asset_date, str):
            asset_date = datetime.strptime(asset_date, "%Y-%m-%d").date()

        years = max((today - asset_date).days / 365, 0)

        # ----- FIX 2: safe numeric conversion -----
        amount = float(a["amount"] or 0)
        annual_return = float(a["annual_return"] or 0)

        # ----- FIX 3: calculate current value -----
        a["current_value"] = round(
            amount * ((1 + annual_return / 100) ** years),
            2
        )

    return assets




def get_assets_by_category(uid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT category, SUM(amount)
        FROM assets
        WHERE uid=%s
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """, (uid,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [r[0] for r in rows], [float(r[1]) for r in rows]

def insert_asset(uid, asset_type,asset_name, category, amount, annual_return, asset_date):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO assets
        (uid, asset_type, asset_name, category, amount, annual_return_percent, purchase_date)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (uid, asset_type, asset_name, category, amount, annual_return, asset_date))

    conn.commit()
    cur.close()
    conn.close()

# ---------- UPDATE ASSET ----------
def update_asset(uid, asset_id, asset_type, asset_name, category,
                 amount, annual_return, purchase_date):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE assets
        SET asset_type=%s,
            asset_name=%s,
            category=%s,
            amount=%s,
            annual_return_percent=%s,
            purchase_date=%s
        WHERE asset_id=%s and uid=%s
    """, (
        asset_type, asset_name, category,
        amount, annual_return, purchase_date, asset_id, uid
    ))

    conn.commit()
    cur.close()
    conn.close()

def delete_asset(uid, asset_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM assets
        WHERE asset_id=%s AND uid=%s
    """, (asset_id, uid))

    conn.commit()
    cur.close()
    conn.close()

def delete_expense(uid, expense_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM expenses
        WHERE expense_id=%s AND uid=%s
    """, (expense_id, uid))

    conn.commit()
    cur.close()
    conn.close()

def update_expense(uid, expense_id, title, category, amount, date, notes):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE expenses
        SET expense_title=%s,
            category=%s,
            amount=%s,
            expense_date=%s,
            note=%s
        WHERE expense_id=%s AND uid=%s
    """, (
        title, category, amount, date, notes,
        expense_id, uid
    ))

    conn.commit()
    cur.close()
    conn.close()

def get_income_transactions(uid, start_date=None, end_date=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    query = """
        SELECT income_id, source, amount, income_date, notes
        FROM income
        WHERE uid=%s
    """
    params = [uid]
    if start_date and end_date:
        query += " AND income_date BETWEEN %s AND %s"
        params.extend([start_date, end_date])

    cur.execute(query, tuple(params))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def delete_income(uid, income_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM income
        WHERE income_id=%s AND uid=%s
    """, (income_id, uid))

    conn.commit()
    cur.close()
    conn.close()

def update_income(uid, income_id, source, amount, income_date, notes):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE income
        SET source=%s,
            amount=%s,
            income_date=%s,
            notes=%s
        WHERE income_id=%s AND uid=%s
    """, (
        source, amount, income_date, notes,
        income_id, uid
    ))

    conn.commit()
    cur.close()
    conn.close()

def get_user_by_id(uid):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE uid=%s", (uid,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def update_user_profile(uid, first_name, last_name):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET first_name=%s,
            last_name=%s
        WHERE uid=%s
    """, (first_name, last_name,uid))

    conn.commit()
    cur.close()
    conn.close()

def update_user_password(uid, password):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET password=%s
        WHERE uid=%s
    """, (password, uid))

    conn.commit()
    cur.close()
    conn.close()

def update_user_email(uid, email):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET email=%s
        WHERE uid=%s
    """, (email, uid))

    conn.commit()
    cur.close()
    conn.close()

def delete_user_completely(uid):
    conn = get_connection()
    cur = conn.cursor()

    tables = [
        "asset_history",
        "assets",
        "expense_update_history",
        "expenses",
        "income_history",
        "income",
        "users"
    ]

    for table in tables:
        cur.execute(f"DELETE FROM {table} WHERE uid=%s", (uid,))

    conn.commit()
    conn.close()
    cur.close()

def get_expense_by_category_dict(uid):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT category, SUM(amount) AS total
        FROM expenses
        WHERE uid = %s
        GROUP BY category
    """, (uid,))

    return {row["category"]: float(row["total"]) for row in cur.fetchall()}

def get_current_month_expense_by_category_dict(uid):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT category, SUM(amount) AS total
        FROM expenses
        WHERE uid = %s
          AND MONTH(expense_date) = MONTH(CURRENT_DATE())
          AND YEAR(expense_date) = YEAR(CURRENT_DATE())
        GROUP BY category
    """, (uid,))

    return {row["category"]: float(row["total"]) for row in cur.fetchall()}


def get_goals(uid):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM goals WHERE uid=%s", (uid,))
    goals = cur.fetchall()
    
    for g in goals:
        # Avoid division by zero if target is 0
        target = float(g['target_amount']) if g['target_amount'] > 0 else 1
        saved = float(g['saved_amount'])
        # Calculate the percentage
        g['percentage'] = min(round((saved / target) * 100, 2), 100)
        
    cur.close()
    conn.close()
    return goals

def update_goal_savings(uid, goal_id, amount):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE goals 
        SET saved_amount = saved_amount + %s 
        WHERE goal_id = %s AND uid = %s
    """, (amount, goal_id, uid))
    conn.commit()
    cur.close()
    conn.close()

def remove_goal(uid, goal_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM goals WHERE goal_id=%s AND uid=%s", (goal_id, uid))
    conn.commit()
    cur.close()
    conn.close()
def insert_new_goal(uid, name, target, deadline):
    conn = get_connection()
    cur = conn.cursor()
    
    query = """
        INSERT INTO goals (uid, goal_name, target_amount, saved_amount, start_date, target_date)
        VALUES (%s, %s, %s, 0.00, CURDATE(), %s)
    """
    cur.execute(query, (uid, name, target, deadline))
    conn.commit()
    cur.close()
    conn.close()
    
def get_recurring_payments(uid):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM recurring_payments WHERE uid=%s ORDER BY billing_date ASC", (uid,))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def insert_recurring(uid, title, amount, category, billing_date, start_date, end_date):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO recurring_payments (uid, title, amount, category, billing_date, start_date, end_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (uid, title, amount, category, billing_date, start_date, end_date if end_date else None))
    conn.commit()
    cur.close()
    conn.close()

def update_recurring(uid, payment_id, title, amount, category, billing_date, start_date, end_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE recurring_payments
        SET title=%s,
            amount=%s,
            category=%s,
            billing_date=%s,
            start_date=%s,
            end_date=%s
        WHERE payment_id=%s AND uid=%s
    """, (title, amount, category, billing_date, start_date, end_date if end_date else None, payment_id, uid))
    conn.commit()
    cur.close()
    conn.close()
def delete_recurring_payment(uid, payment_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM recurring_payments 
        WHERE payment_id=%s AND uid=%s
    """, (payment_id, uid))
    conn.commit()
    cur.close()
    conn.close()

def update_recurring_status(uid, payment_id, new_status):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE recurring_payments 
        SET status=%s 
        WHERE payment_id=%s AND uid=%s
    """, (new_status, payment_id, uid))
    conn.commit()
    cur.close()
    conn.close()

def apply_recurring_to_expenses(uid, today):
    """
    If a recurring payment is due today, insert it into expenses once per month.
    Idempotent via a unique note token: recurring:<payment_id>:<YYYY-MM>.
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute(
        """
        SELECT payment_id, title, amount, category, billing_date, start_date, end_date,
               COALESCE(status, 'active') AS status
        FROM recurring_payments
        WHERE uid=%s
        """,
        (uid,)
    )
    payments = cur.fetchall()

    expense_cur = conn.cursor()

    for p in payments:
        if p.get("status") and str(p["status"]).lower() != "active":
            continue

        billing_day = int(p["billing_date"])
        if today.day != billing_day:
            continue

        start_date = p.get("start_date")
        end_date = p.get("end_date")

        
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime):
            end_date = end_date.date()

        if start_date and today < start_date:
            continue
        if end_date and today > end_date:
            continue

        token = f"recurring:{p['payment_id']}:{today.strftime('%Y-%m')}"

        expense_cur.execute(
            "SELECT 1 FROM expenses WHERE uid=%s AND note=%s LIMIT 1",
            (uid, token)
        )
        if expense_cur.fetchone():
            continue

        expense_cur.execute(
            """
            INSERT INTO expenses (uid, expense_title, category, amount, expense_date, note)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                uid,
                p["title"],
                p["category"],
                float(p["amount"]),
                today.strftime("%Y-%m-%d"),
                token,
            ),
        )

    conn.commit()
    expense_cur.close()
    cur.close()
    conn.close()





# ---------------- NET WORTH ----------------

def get_total_assets_current_value(uid):
    assets = get_assets(uid)
    total = 0.0
    for a in assets:
        total += float(a.get("current_value") or 0)
    return total

