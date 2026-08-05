# MoneyWise | Smart Finance Manager

MoneyWise is a comprehensive personal finance management application built with Flask. It helps users track their income, expenses, assets, and financial goals with a modern, dark-themed dashboard and interactive data visualizations.

## 🚀 Features

- **User Authentication**: Secure signup and login with OTP verification via email.
- **Dashboard**: High-level overview of monthly income, expenses, savings, and net worth.
- **Income & Expense Tracking**: Detailed transaction logging with category-wise breakdowns.
- **Asset Management**: Track investments and assets with automatic current value estimation based on annual returns.
- **Budgeting**: Visualize budget vs. actual spending using the 50-30-20 rule.
- **Recurring Payments**: Manage bills and EMIs with automatic expense logging.
- **Financial Goals**: Set and track progress toward specific savings goals.
- **Data Visualization**: Dynamic charts and graphs powered by Matplotlib.
- **CSV Export**: Download transaction history for income and expenses.

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **Database**: MySQL (handled via `db.py`)
- **Frontend**: HTML5, CSS3 (Custom Dark Theme), Bootstrap 5, Tailwind CSS
- **Visualization**: Matplotlib
- **Email Service**: Flask-Mail (Gmail SMTP)

## 📦 Project Structure

```text
├── app.py              # Main Flask application and routes
├── db.py               # Database connection and CRUD operations
├── graph.py            # Matplotlib chart generation logic
├── static/             # Static assets (images, custom CSS)
└── templates/          # Jinja2 HTML templates
```

## ⚙️ Setup & Installation

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd flask/final
    ```

2.  **Install Dependencies**
    ```bash
    pip install flask flask-mail pandas matplotlib mysql-connector-python python-dateutil
    ```

3.  **Database Configuration**
    - Ensure you have a MySQL server running.
    - Configure your database credentials in `db.py`.
    - Create the required tables (users, income, expenses, assets, goals, recurring_payments).

4.  **Email Configuration**
    - Update `app.config['MAIL_USERNAME']` and `app.config['MAIL_PASSWORD']` in `app.py` with your Gmail credentials (use an App Password).

5.  **Run the Application**
    ```bash
    python app.py
    ```
    The app will be available at `http://127.0.0.1:5000`.

## 🔒 Security Features

- **OTP Verification**: Email-based OTP for registration and password recovery.
- **Password Strength**: Server-side and client-side validation for strong passwords.
- **Session Management**: Secure user sessions for data privacy.
- **Input Validation**: Server-side validation for email formats and dates (no future dates for transactions).

## 📊 Visualizations

- **Income/Expense Trend**: Line graphs showing monthly financial flow.
- **Expense Distribution**: Pie charts for category-wise spending.
- **Budget Analysis**: Bar charts comparing planned vs. actual spending.
- **Asset Growth**: Comparison of invested amount vs. current value.
