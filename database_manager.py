import os
import sqlite3
import shutil
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "accounts.db")

def init_database():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_number TEXT PRIMARY KEY, name TEXT NOT NULL, balance REAL NOT NULL,
                password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user',
                failed_attempts INTEGER NOT NULL DEFAULT 0, is_locked INTEGER NOT NULL DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, account_number TEXT NOT NULL, date TEXT NOT NULL,
                trans_type TEXT NOT NULL, amount REAL NOT NULL, balance REAL NOT NULL,
                FOREIGN KEY (account_number) REFERENCES accounts (account_number)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, admin_user TEXT NOT NULL,
                action TEXT NOT NULL, target_user TEXT, details TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY, value TEXT NOT NULL
            )
        """)
        cursor.execute("INSERT OR IGNORE INTO system_config (key, value) VALUES ('interest_rate', '2.5')")
        conn.commit()
def backup_database():
    try:
        backup_file = os.path.join(SCRIPT_DIR, f"accounts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        shutil.copy(DB_FILE, backup_file)
        print(f"Backup successfully created: {backup_file}")
    except FileNotFoundError:
        print("Database file not found. Nothing to back up.")
    except Exception as e:
        print(f"An error occurred during backup: {e}")
def load_all_accounts():
    if not os.path.exists(DB_FILE): return {}
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts")
        return {row[0]: row for row in cursor.fetchall()}
def load_transactions_for_account(account_number):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT date, trans_type, amount, balance FROM transactions WHERE account_number = ? ORDER BY date DESC", (account_number,))
        return [(datetime.fromisoformat(date), t_type, amt, bal) for date, t_type, amt, bal in cursor.fetchall()]
def create_new_account(account):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?, ?)", (
                account.account_number, account.name, account.balance, account.password_hash,
                account.role, account.failed_attempts, int(account.is_locked)
            ))
            initial_transaction = account.transactions[0]
            cursor.execute("INSERT INTO transactions (account_number, date, trans_type, amount, balance) VALUES (?, ?, ?, ?, ?)", (
                account.account_number, initial_transaction[0].isoformat(), initial_transaction[1], initial_transaction[2], initial_transaction[3]
            ))
            conn.commit()
            return True
    except sqlite3.IntegrityError: return False
def delete_account_and_transactions(account_number):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE account_number = ?", (account_number,))
            cursor.execute("DELETE FROM accounts WHERE account_number = ?", (account_number,))
            conn.commit()
            return True
    except sqlite3.Error as e:
        print(f"DB Error on delete: {e}")
        return False
def save_new_transaction(account_number, transaction):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO transactions (account_number, date, trans_type, amount, balance) VALUES (?, ?, ?, ?, ?)", (
                account_number, transaction[0].isoformat(), transaction[1], transaction[2], transaction[3]))
            conn.commit()
    except sqlite3.Error as e: print(f"Database error saving transaction: {e}")
def update_account_state(account):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE accounts SET name = ?, balance = ?, failed_attempts = ?, is_locked = ? WHERE account_number = ?", (
                account.name, account.balance, account.failed_attempts, int(account.is_locked), account.account_number))
            conn.commit()
    except sqlite3.Error as e: print(f"Database error updating account state: {e}")
def update_password(account_number, new_password_hash):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE accounts SET password_hash = ? WHERE account_number = ?", (new_password_hash, account_number))
            conn.commit()
            return True
    except sqlite3.Error as e:
        print(f"Database error updating password: {e}")
        return False
def execute_transfer(from_account, to_account):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE accounts SET balance = ? WHERE account_number = ?", (from_account.balance, from_account.account_number))
        cursor.execute("UPDATE accounts SET balance = ? WHERE account_number = ?", (to_account.balance, to_account.account_number))
        from_transaction, to_transaction = from_account.transactions[-1], to_account.transactions[-1]
        cursor.execute("INSERT INTO transactions (account_number, date, trans_type, amount, balance) VALUES (?, ?, ?, ?, ?)",
            (from_account.account_number, from_transaction[0].isoformat(), from_transaction[1], from_transaction[2], from_transaction[3]))
        cursor.execute("INSERT INTO transactions (account_number, date, trans_type, amount, balance) VALUES (?, ?, ?, ?, ?)",
            (to_account.account_number, to_transaction[0].isoformat(), to_transaction[1], to_transaction[2], to_transaction[3]))
        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Transfer failed due to a database error: {e}")
        return False
    finally: conn.close()
def log_admin_action(admin_user, action, target_user, details=""):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()
            cursor.execute("INSERT INTO audit_log (timestamp, admin_user, action, target_user, details) VALUES (?, ?, ?, ?, ?)",
                        (timestamp, admin_user, action, target_user, details))
            conn.commit()
    except sqlite3.Error as e: print(f"Failed to write to audit log: {e}")
def get_audit_log():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, admin_user, action, target_user, details FROM audit_log ORDER BY timestamp DESC")
        return cursor.fetchall()
def get_interest_rate():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_config WHERE key = 'interest_rate'")
        return float(cursor.fetchone()[0])
def set_interest_rate(rate):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE system_config SET value = ? WHERE key = 'interest_rate'", (str(rate),))
        conn.commit()