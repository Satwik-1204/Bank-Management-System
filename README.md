# Python Bank Management System 🏦

A complete, secure, and modern desktop application for bank account management, built with Python and Tkinter. This project features separate dashboards for users and administrators, complete with robust backend logic and a secure SQLite database.

## Core Features

### 👤 User Features
* **Secure Account Creation:** New users can securely create an account with a strong password.
* **Encrypted Login:** Uses **bcrypt** for hashing and verifying passwords (no plaintext passwords are stored).
* **Transaction Management:** Perform core banking operations:
    * **Deposit:** Add funds to your account.
    * **Withdraw:** Withdraw funds with insufficient balance checks.
    * **Fund Transfer:** Securely transfer money to other users.
* **Account Dashboard:** A clean, tabbed interface to view:
    * **Account Summary:** See your balance and details at a glance.
    * **Transaction History:** View a full history of all your transactions.
    * **Profile Management:** Change your account name and password.
* **Reporting:**
    * Generate a full **PDF Bank Statement**.
    * Export transaction history to a **CSV file**.
* **Utilities:**
    * **Loan Calculator:** An EMI calculator to plan loans.
    * **Low Balance Alerts:** Get a visual warning on login if your balance is low.

### 🛡️ Administrator Features
* **Admin Dashboard:** A separate, powerful dashboard for system management.
* **User Management:**
    * View a list of all user accounts, balances, and statuses.
    * **Unlock Accounts:** Manually unlock user accounts that are locked due to failed login attempts.
    * **Delete Accounts:** Securely delete a user and all their associated data.
* **System Financials:**
    * Set the global annual interest rate.
    * Apply interest to all eligible user accounts with a single click.
* **Audit Log:** A read-only log that tracks all critical admin actions (e.g., account deletions, interest application) for security and accountability.

---

## 🛠️ Tech Stack & Requirements

This project is built entirely in Python.

* **Backend:** Python 3
* **Database:** `sqlite3` (built-in)
* **GUI:** `tkinter` & `ttkbootstrap` (for the modern UI)
* **Security:** `bcrypt` (for password hashing)
* **Reporting:** `reportlab` (for PDF generation)

---

## 🚀 How to Run This Project

### 1. Prerequisites
You must have Python 3 installed on your system.

### 2. Clone the Repository
```bash
git clone [https://github.com/Satwik-1204/python-bank-management-system.git](https://github.com/Satwik-1204/python-bank-management-system.git)
cd python-bank-management-system
