from datetime import datetime    
from flask import Flask, render_template, request, redirect, url_for, session, flash,Response
from flask_mail import Mail, Message
from dateutil.relativedelta import relativedelta
from graph import asset_amount_vs_current_by_category,expense_category_pie_chart,category_budget_vs_used,grep
import random
import pandas as pd
import io
import re

import db 
from graph import grep   

app = Flask(__name__)
app.secret_key = "moneywisesecret"

def parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

def is_not_future_date(s):
    d = parse_date(s)
    if not d:
        return False
    return d <= datetime.now().date()
# ---------------- MAIL CONFIG ----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'moneywise433@gmail.com'
app.config['MAIL_PASSWORD'] = 'roqe mpbb kbys auzc'  # Use app password for Gmail

mail = Mail(app)

ALLOWED_EMAIL_DOMAINS = {"gmail.com", "yahoo.com"}

def is_valid_allowed_email(email: str) -> bool:
    if not email:
        return False
    email = email.strip().lower()
    # Basic email shape
    if not re.match(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$", email):
        return False
    domain = email.split("@")[-1]
    return domain in ALLOWED_EMAIL_DOMAINS


def is_strong_password(password: str) -> bool:
    """
    At least:
    - 1 uppercase letter
    - 1 digit
    - 1 special character
    - no spaces
    """
    if not password:
        return False
    if " " in password:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[^\w]", password):
        return False
    return True

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("home.html")

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        first = request.form["first_name"]
        last = request.form["last_name"]
        email = request.form["email"].strip().lower()

        if not is_valid_allowed_email(email):
            flash("Please enter a valid email ending with @gmail.com or @yahoo.com.", "danger")
            return redirect(url_for("signup"))

        if db.get_user_by_email(email):
            flash("Email already registered!", "danger")
            return redirect(url_for("signup"))

        otp = str(random.randint(100000, 999999))
        db.create_user(first, last, email, otp)
        
        try:
            msg = Message(
                "MoneyWise OTP Verification",
                sender=app.config['MAIL_USERNAME'],
                recipients=[email]
            )
            msg.body = f"Your MoneyWise OTP is: {otp}"
            mail.send(msg)
        except Exception as e:
            print(f"Failed to send OTP email: {e}")
            flash("Failed to send OTP. Please check email configuration.", "danger")
            return redirect(url_for("signup"))

        session["verify_email"] = email
        return redirect(url_for("verify_otp"))

    return render_template("signup.html")

# ---------------- VERIFY OTP ----------------
@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():

    #  If OTP already used → block page
    if "verify_email" not in session:
        return redirect(url_for("login"))

    email = session["verify_email"]
    if not is_valid_allowed_email(email):
        session.pop("verify_email", None)
        session.pop("otp_verified", None)
        flash("Invalid email. Please try again.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        otp = (
            request.form["otp1"] +
            request.form["otp2"] +
            request.form["otp3"] +
            request.form["otp4"] +
            request.form["otp5"] +
            request.form["otp6"]
        )

        if db.verify_user_otp(email, otp):
            # Mark OTP as done (but keep email for password page)
            session["otp_verified"] = True
            return redirect(url_for("create_password"))

        flash("Invalid OTP", "danger")

    return render_template("verify_otp.html", email=email)


# ---------------- RESEND OTP ----------------
@app.route("/resend-otp")
def resend_otp():
    email = session.get("verify_email")
    if not email:
        return redirect(url_for("signup"))
    if not is_valid_allowed_email(email):
        session.pop("verify_email", None)
        flash("Invalid email. Please try again.", "danger")
        return redirect(url_for("signup"))

    otp = str(random.randint(100000, 999999))
    db.update_otp(email, otp)

    try:
        msg = Message(
            "MoneyWise OTP (Resent)",
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = f"Your new OTP is: {otp}"
        mail.send(msg)
    except Exception as e:
        print(f"Failed to resend OTP email: {e}")
        flash("Failed to resend OTP. Please try again.", "danger")
        return redirect(url_for("verify_otp"))

    flash("OTP resent successfully!", "success")
    return redirect(url_for("verify_otp"))

# ---------------- CREATE PASSWORD ----------------
@app.route("/create-password", methods=["GET", "POST"])
def create_password():

    #  OTP must be verified first
    if not session.get("otp_verified"):
        return redirect(url_for("login"))

    email = session.get("verify_email")

    if request.method == "POST":
        password = request.form["password"]

        if not is_strong_password(password):
            flash("Password must have at least 1 uppercase letter, 1 digit, 1 special character, and no spaces.", "danger")
            return redirect(url_for("create_password"))

        db.set_user_password(email, password)

        
        session.clear()

        flash("Password updated successfully! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("create_password.html")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"].strip().lower()

        if not is_valid_allowed_email(email):
            flash("Please enter a valid email ending with @gmail.com or @yahoo.com.", "danger")
            return redirect(url_for("forgot_password"))

        user = db.get_user_by_email(email)

       
        if not user:
            flash("Email not found. Please create an account.", "warning")
            return redirect(url_for("signup"))

        
        otp = str(random.randint(100000, 999999))
        db.update_otp(email, otp)

        try:
            msg = Message(
                "MoneyWise Password Reset OTP",
                sender=app.config['MAIL_USERNAME'],
                recipients=[email]
            )
            msg.body = f"Your MoneyWise OTP is: {otp}"
            mail.send(msg)
        except Exception as e:
            print("OTP mail error:", e)
            flash("Failed to send OTP. Try again.", "danger")
            return redirect(url_for("forgot_password"))

        session["verify_email"] = email
        session["otp_purpose"] = "forgot"

        return redirect(url_for("verify_otp"))

    return render_template("forgot.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = db.get_user_by_email(email)
        if user and user["password"] and user["password"] == password:
            session["uid"] = user["uid"]
            session["user_email"] = user["email"]
            return redirect(url_for("dashboard"))

        flash("Invalid login credentials", "danger")

    return render_template("login.html")



# ---------- CARRY FORWARD ----------
def carry_forward(data, months=12):
    result = {}
    last_value = 0
    start = datetime.today().replace(day=1)

    for i in range(months):
        m = (start - relativedelta(months=months-1-i)).strftime('%Y-%m')
        if m in data:
            last_value = data[m]
        result[m] = last_value
    return result




@app.route("/dashboard" , methods=["GET", "POST"]  )
def dashboard():
    if "uid" not in session:
        return redirect(url_for("login"))

    uid = session["uid"]
    try:
        db.apply_recurring_to_expenses(uid, datetime.now().date())
    except Exception as e:
        print(f"Recurring apply error: {e}")



        
  
    income_raw = db.get_monthly_income(uid)
    expense_raw = db.get_monthly_expense(uid)
    income_cf = carry_forward(income_raw)
    expense_cf = carry_forward(expense_raw)
    months = list(income_cf.keys())
    income_values = list(income_cf.values())
    expense_values = [expense_cf[m] for m in months]

    income, expense = db.get_current_month_totals(uid)
    income = float(income or 0)
    expense = float(expense or 0)
    savings = income - expense

    # Graph & Top Expenses
    chart = grep("Finance").grap(months, income_values, expense_values)
    top_expenses = db.get_top_3_expenses(uid)

    
    total_assets_value = 0.0
    
    try:
        total_assets_value = db.get_total_assets_current_value(uid)
    except Exception as e:
        print(f"Net worth assets error: {e}")
    

    net_worth = float(total_assets_value) 
    needs = income * 0.5
    wants = income * 0.3
    saving_rule = income * 0.2

    return render_template(
        "dashboard.html",
        income=income,
        expense=expense,
        savings=savings,
        net_worth=net_worth,
        chart=chart,
        top_expenses=top_expenses,
        needs=needs,
        wants=wants,
        saving_rule=saving_rule,
        today_date=datetime.now()
    )

@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/expenses", methods=["GET", "POST"])
def expenses():
    uid = session.get("uid")
    if not uid:
        return redirect(url_for("home"))

    
    try:
        db.apply_recurring_to_expenses(uid, datetime.now().date())
    except Exception as e:
        print(f"Recurring apply error: {e}")

    if request.method == "POST":
        if "expense_id" in request.form:
            if not is_not_future_date(request.form["expense_date"]):
                flash("Expense Date cannot be in the future", "danger")
                return redirect(url_for("expenses"))

            cat = request.form.get("category", "")
            if cat == "Other":
                custom = request.form.get("custom_category", "").strip()
                if custom:
                    cat = custom
            db.update_expense(
                session["uid"],
                int(request.form["expense_id"]),
                request.form["expense_title"],
                cat,
                float(request.form["amount"]),
                request.form["expense_date"],
                request.form["notes"]
            )
        elif "expense_id1" in request.form:
            db.delete_expense(
                session["uid"],
                int(request.form["expense_id1"])
            )
        else: 
            if not is_not_future_date(request.form["expense_date"]):
                flash("Expense Date cannot be in the future", "danger")
                return redirect(url_for("expenses"))
            cat = request.form.get("category", "")
            if cat == "Other":
                custom = request.form.get("custom_category", "").strip()
                if custom:
                    cat = custom
            db.insert_expense(
                session["uid"],
                request.form["expense_title"],
                cat,
                float(request.form["amount"]),
                request.form["expense_date"],
                request.form["notes"]
            )
    expenses = db.get_expense_by_category(uid)
    chart = expense_category_pie_chart(expenses)
    transactions = db.get_expense_transactions(uid)

    return render_template(
        "expenses.html",
        chart=chart,
        transactions=transactions
    )


@app.route("/income", methods=["GET", "POST"])
def income():
    uid = session.get("uid")
    if not uid:
        return redirect(url_for("home"))

    if request.method == "POST":
        if "income_id" in request.form:
            if not is_not_future_date(request.form["income_date"]):
                flash("Income Date cannot be in the future", "danger")
                return redirect(url_for("income"))
            db.update_income(
                session["uid"],
                int(request.form["income_id"]),
                request.form["Source"],
                float(request.form["amount"]),
                request.form["income_date"],
                request.form["notes"]
            )
        elif "income_id1" in request.form:
            db.delete_income(
                session["uid"],
                int(request.form["income_id1"])
            )
        else: 
            if not is_not_future_date(request.form["income_date"]):
                flash("Income Date cannot be in the future", "danger")
                return redirect(url_for("income"))
            db.insert_income(
                session["uid"],
                request.form["Source"],
                float(request.form["amount"]),
                request.form["income_date"],
                request.form["notes"]
            )
    
  
    transactions = db.get_income_transactions(uid)

    return render_template(
        "income.html",
        
        transactions=transactions
    )

@app.route("/assets", methods=["GET", "POST"])
def assets():
    uid = session.get("uid")
    if not uid:
        return redirect(url_for("home"))
    


    if request.method == "POST":
        if "asset_id" in request.form:
            if not is_not_future_date(request.form["asset_date"]):
                flash("Purchase Date cannot be in the future", "danger")
                return redirect(url_for("assets"))
            db.update_asset(
                session["uid"],
                int(request.form["asset_id"]),
                request.form["asset_type"],
                request.form["asset_name"],
                request.form["category"],
                float(request.form["amount"]),
                float(request.form.get("annual_return", 0)),
                request.form["asset_date"]
            )
        elif "asset_id1" in request.form:
            db.delete_asset(
                session["uid"],
                int(request.form["asset_id1"])
            )
        else:
            if not is_not_future_date(request.form["asset_date"]):
                flash("Purchase Date cannot be in the future", "danger")
                return redirect(url_for("assets"))
            db.insert_asset(
                session["uid"],
                request.form["asset_type"],
                request.form["asset_name"],
                request.form["category"],
                float(request.form["amount"]),
                float(request.form.get("annual_return", 0)),
                request.form["asset_date"]
            )
    assets =db.get_assets(uid)
    chart = asset_amount_vs_current_by_category(assets)
    transactions = db.get_assets(uid)
    
    return render_template(
        "asset.html",
        chart=chart,
        transactions=transactions
    )



@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "uid" not in session:
        return redirect(url_for("login"))

    uid = session["uid"]
    user = db.get_user_by_id(uid)

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_profile":
            db.update_user_profile(
                uid,
                request.form["first_name"],
                request.form["last_name"]
            )
            flash("Profile updated successfully!", "success")

        elif action == "change_password":
            if user["password"] != request.form["current_password"]:
                flash("Current password is incorrect!", "danger")
                return redirect(url_for("settings"))

            new_password = request.form["new_password"]
            if not is_strong_password(new_password):
                flash("New password must have at least 1 uppercase letter, 1 digit, 1 special character, and no spaces.", "danger")
                return redirect(url_for("settings"))

            db.update_user_password(uid, new_password)
            flash("Password updated successfully!", "success")

        elif action == "delete_account":
            db.delete_user_completely(uid)
            session.clear()
            flash("Account deleted permanently.", "success")
            return redirect(url_for("login"))

        return redirect(url_for("settings"))

    return render_template("setting.html", user=user)

from graph import category_budget_vs_used

@app.route("/budget")
def budget():
    uid = session.get("uid")
    if not uid:
        return redirect(url_for("login"))

    income, _ = db.get_current_month_totals(uid)
    income = float(income or 0)

    expense_map = db.get_current_month_expense_by_category_dict(uid)

    chart = None
    try:
        chart = category_budget_vs_used(income, expense_map)
    except Exception as e:
        print(f"Error generating budget chart: {e}")
        chart = None

    return render_template(
        "budget.html",
        chart=chart,
        needs=income * 0.5,
        wants=income * 0.3,
        savings=income * 0.2,
        today_date=datetime.now()
    )
# ---------------- CSV Export ---------------- #

@app.route("/download-income-csv")
def download_income_csv():
    if "uid" not in session:
        return redirect(url_for("login"))

    uid = session["uid"]
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    if not start_date or not end_date:
        flash("Please select Start Date and End Date for CSV download.", "warning")
        return redirect(url_for("income"))

    transactions = db.get_income_transactions(uid, start_date=start_date, end_date=end_date)

   
    if transactions and isinstance(transactions[0], dict):
        df = pd.DataFrame(transactions, columns=["income_id", "source", "amount", "income_date", "notes"])
    else:
        df = pd.DataFrame(transactions or [], columns=["ID", "Source", "Amount", "Date", "Notes"])

    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    filename = f"income_{start_date}_to_{end_date}.csv"

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@app.route("/download-expense-csv")
def download_expense_csv():
    if "uid" not in session:
        return redirect(url_for("login"))

    uid = session["uid"]
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    if not start_date or not end_date:
        flash("Please select Start Date and End Date for CSV download.", "warning")
        return redirect(url_for("expenses"))

    transactions = db.get_expense_transactions(uid, start_date=start_date, end_date=end_date)

    if transactions and isinstance(transactions[0], dict):
        df = pd.DataFrame(transactions, columns=["expense_id", "expense_title", "category", "amount", "expense_date", "notes"])
    else:
        df = pd.DataFrame(transactions or [], columns=["ID", "Title", "Category", "Amount", "Date", "Notes"])

    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    filename = f"expenses_{start_date}_to_{end_date}.csv"

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@app.route("/download-assets-csv")
def download_assets_csv():
    if "uid" not in session:
        return redirect(url_for("login"))

    uid = session["uid"]
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    if not start_date or not end_date:
        flash("Please select Start Date and End Date for CSV download.", "warning")
        return redirect(url_for("assets"))

    transactions = db.get_assets(uid, start_date=start_date, end_date=end_date)

    if transactions and isinstance(transactions[0], dict):
        df = pd.DataFrame(transactions)
    else:
        df = pd.DataFrame(transactions, columns=[
            "ID", "Type", "Name", "Category",
            "Amount", "Annual Return", "Date","current_value"
        ])

    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    filename = f"assets_{start_date}_to_{end_date}.csv"

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )


# -----goals-----
@app.route('/goals' ,methods=['GET', 'POST'])
def goals():
    if 'uid' not in session:
        return redirect('/login')
    uid = session['uid']
    if request.method == 'POST':
        name = request.form.get('goal_name')
        target = request.form.get('target_amount')
        deadline = request.form.get('target_date')
        db.insert_new_goal(uid, name, target, deadline)
    user_goals = db.get_goals(uid)
    return render_template('goals.html', goals=user_goals)


@app.route('/add-saving/<int:goal_id>', methods=['POST'])
def add_saving(goal_id):
    if 'uid' not in session:
        return redirect('/login')
    
    uid = session['uid']
    amount_to_add = float(request.form.get('amount', 0))
    
   
    goals = db.get_goals(uid)
   
    current_goal = next((g for g in goals if g['goal_id'] == goal_id), None)
    
    if current_goal:
       
        if current_goal['saved_amount'] >= current_goal['target_amount']:
            flash(f"Goal '{current_goal['goal_name']}' is already fulfilled!", "info")
        else:
           
            db.update_goal_savings(uid, goal_id, amount_to_add)
            
            
            updated_goals = db.get_goals(uid)
            new_data = next((g for g in updated_goals if g['goal_id'] == goal_id), None)
            if new_data and new_data['saved_amount'] >= new_data['target_amount']:
                flash(f"Congratulations! You've reached 100% for '{new_data['goal_name']}'!", "success")
            else:
                flash("Saving added successfully!", "success")
                
    return redirect('/goals')

@app.route('/delete-goal/<int:goal_id>')
def delete_goal(goal_id):
    uid = session['uid']
    db.remove_goal(uid, goal_id)
    return redirect('/goals')


# --------recuring------------
@app.route('/recurring' ,methods=['GET', 'POST'])
def recurring_page():
    if 'uid' not in session: return redirect('/login')
    if request.method == 'POST':
        
        today = datetime.now().date()
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except Exception:
            flash("Invalid start date.", "danger")
            return redirect('/recurring')

        if start_date > today:
            flash("Start date cannot be after today's date.", "danger")
            return redirect('/recurring')

        category = request.form.get('category')
        if category == "EMI":
            if not end_date_str:
                flash("End date is required for EMI.", "danger")
                return redirect('/recurring')
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except Exception:
                flash("Invalid end date.", "danger")
                return redirect('/recurring')
            if end_date < start_date:
                flash("End date cannot be before start date.", "danger")
                return redirect('/recurring')

        title = request.form.get('title')
        amount = request.form.get('amount')
        billing_date = request.form.get('billing_date')

        payment_id = request.form.get('payment_id')
        if payment_id:
            db.update_recurring(
                session['uid'],
                int(payment_id),
                title,
                amount,
                category,
                billing_date,
                start_date_str,
                end_date_str
            )
            flash("Recurring payment updated!", "success")
        else:
            db.insert_recurring(
                session['uid'], 
                title,
                amount,
                category,
                billing_date,
                start_date_str,
                end_date_str
            )
            flash("Recurring payment added!", "success")

        return redirect('/recurring')


    try:
        db.apply_recurring_to_expenses(session['uid'], datetime.now().date())
    except Exception as e:
        print(f"Recurring apply error: {e}")

    payments = db.get_recurring_payments(session['uid'])
    return render_template('recurring.html', payments=payments)


@app.route('/delete-recurring/<int:payment_id>')
def delete_recurring(payment_id):
    if 'uid' not in session:
        return redirect('/login')
    uid = session['uid']
    db.delete_recurring_payment(uid, payment_id)
    flash("Recurring payment removed successfully.", "danger")
    return redirect('/recurring')


@app.route('/update-recurring-status/<int:payment_id>/<string:status>')
def update_status(payment_id, status):
    if 'uid' not in session:
        return redirect('/login')
    uid = session['uid']
    db.update_recurring_status(uid, payment_id, status)
    flash(f"Payment status updated to {status}.", "info")
    return redirect('/recurring')


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)



