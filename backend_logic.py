import database_manager as db
from models import Account, is_strong_password, hash_password
from datetime import datetime
import math

class BankSystem:
    def __init__(self):
        self.accounts = {}
        self.current_user = None
        db.init_database()
        self._load_accounts()
        self._ensure_admin_exists()
    def _load_accounts(self):
        self.accounts.clear()
        accounts_data = db.load_all_accounts()
        for acc_num, data in accounts_data.items():
            acc_num, name, balance, pwd_hash, role, f_attempts, locked = data
            account = Account(name, acc_num, balance, pwd_hash, role, f_attempts, locked)
            account.transactions = db.load_transactions_for_account(acc_num)
            self.accounts[acc_num] = account
    def _ensure_admin_exists(self):
        if "admin" not in self.accounts:
            print("No admin account found. Creating a default admin...")
            default_pass = "Admin@1234"
            password_hash = hash_password(default_pass)
            admin_acc = Account("Administrator", "admin", 0, password_hash, role='admin')
            admin_acc.transactions.append((datetime.now(), "Initial Deposit", 0, 0))
            if db.create_new_account(admin_acc):
                self.accounts["admin"] = admin_acc
                print(f"Default admin created. User: admin, Pass: {default_pass}")
    def login(self, acc_number, password):
        alert_message = None
        if acc_number not in self.accounts: return "Account not found.", None, None
        account = self.accounts[acc_number]
        if account.is_locked: return "This account is locked.", None, None
        if account.verify_password(password):
            account.reset_failed_attempts()
            db.update_account_state(account)
            self.current_user = account
            if self.current_user.balance < 1000:
                alert_message = f"Warning: Low balance: INR {self.current_user.balance:.2f}"
            return "Login successful.", account, alert_message
        else:
            account.increment_failed_attempts()
            db.update_account_state(account)
            remaining = Account.MAX_FAILED_ATTEMPTS - account.failed_attempts
            return f"Incorrect password. {remaining} attempts remaining.", None, None
    def logout(self):
        self.current_user = None
    def create_account(self, name, acc_number, password, balance):
        if not all(c.isalpha() or c.isspace() or c == '-' for c in name if c): return "Name is invalid."
        if not acc_number.isalnum(): return "Account number must be alphanumeric."
        if acc_number in self.accounts: return "An account with this number already exists."
        is_strong, message = is_strong_password(password)
        if not is_strong: return f"Invalid password: {message}"
        if balance < 0: return "Balance cannot be negative."
        password_hash = hash_password(password)
        account = Account(name, acc_number, balance, password_hash)
        account.transactions.append((datetime.now(), "Initial Deposit", balance, balance))
        if db.create_new_account(account):
            self.accounts[acc_number] = account
            return "Account created successfully! You can now log in."
        else: return "An unexpected error occurred during account creation."
    def get_current_user_details(self):
        if not self.current_user: return "No user logged in."
        return self.current_user
    def deposit(self, amount):
        transaction = self.current_user.deposit(amount)
        if transaction:
            db.save_new_transaction(self.current_user.account_number, transaction)
            db.update_account_state(self.current_user)
            return f"Successfully deposited INR {amount:.2f}."
        else: return "Deposit failed. Amount must be positive."
    def withdraw(self, amount):
        transaction = self.current_user.withdraw(amount)
        if transaction:
            db.save_new_transaction(self.current_user.account_number, transaction)
            db.update_account_state(self.current_user)
            return f"Successfully withdrew INR {amount:.2f}."
        else: return "Withdrawal failed. Check amount and balance."
    def transfer_funds(self, to_acc_number, amount):
        if to_acc_number not in self.accounts: return "Recipient account not found."
        if to_acc_number == self.current_user.account_number: return "Cannot transfer to your own account."
        if amount <= 0: return "Transfer amount must be positive."
        if amount > self.current_user.balance: return "Insufficient balance."
        from_account = self.current_user
        to_account = self.accounts[to_acc_number]
        from_account.balance -= amount
        to_account.balance += amount
        from_account.transactions.append((datetime.now(), "Transfer Out", amount, from_account.balance))
        to_account.transactions.append((datetime.now(), "Transfer In", amount, to_account.balance))
        if db.execute_transfer(from_account, to_account):
            return f"Successfully transferred INR {amount:.2f} to {to_account.name}."
        else:
            from_account.balance += amount
            to_account.balance -= amount
            from_account.transactions.pop()
            to_account.transactions.pop()
            return "Transfer failed due to a database error."
    def update_user_name(self, new_name):
        if not all(c.isalpha() or c.isspace() or c == '-' for c in new_name if c): return "Name is invalid."
        self.current_user.name = new_name
        db.update_account_state(self.current_user)
        return "Name updated successfully."
    def update_user_password(self, old_password, new_password):
        if not self.current_user.verify_password(old_password): return "Current password incorrect."
        is_strong, message = is_strong_password(new_password)
        if not is_strong: return f"Failed to update: {message}"
        self.current_user.password_hash = hash_password(new_password)
        if db.update_password(self.current_user.account_number, self.current_user.password_hash):
            return "Password updated successfully."
        else: return "Failed to update password in database."
    def calculate_loan_emi(self, principal, annual_rate, years):
        if principal <= 0 or annual_rate <= 0 or years <= 0:
            return "Principal, rate, and years must be positive values."
        monthly_rate = (annual_rate / 100) / 12
        months = years * 12
        emi = principal * monthly_rate * (pow(1 + monthly_rate, months)) / (pow(1 + monthly_rate, months) - 1)
        return f"Estimated EMI: INR {emi:.2f} per month."
    def admin_delete_account(self, acc_to_delete):
        acc_to_delete = str(acc_to_delete)
        if acc_to_delete == self.current_user.account_number: return "Admin cannot delete their own account."
        if acc_to_delete not in self.accounts: return "Account not found."
        if db.delete_account_and_transactions(acc_to_delete):
            db.log_admin_action(self.current_user.account_number, "DELETE_ACCOUNT", acc_to_delete)
            del self.accounts[acc_to_delete]
            return f"Account {acc_to_delete} deleted successfully."
        else: return "Failed to delete account from database."
    def admin_unlock_account(self, acc_to_unlock):
        acc_to_unlock = str(acc_to_unlock)
        if acc_to_unlock not in self.accounts: return "Account not found."
        target_account = self.accounts[acc_to_unlock]
        if not target_account.is_locked:
            return f"Account {acc_to_unlock} is already active."
        target_account.reset_failed_attempts()
        db.update_account_state(target_account)
        db.log_admin_action(self.current_user.account_number, "UNLOCK_ACCOUNT", acc_to_unlock)
        return f"Account {acc_to_unlock} has been unlocked."
    def admin_get_all_users_report(self):
        return [acc for acc in self.accounts.values()]
    def admin_apply_interest(self):
        rate = db.get_interest_rate()
        annual_rate = rate / 100
        for acc in self.accounts.values():
            if acc.role == 'user' and acc.balance > 0:
                interest_amount = acc.balance * annual_rate
                acc.deposit(interest_amount)
                t_date, _, t_amt, t_bal = acc.transactions.pop()
                interest_transaction = (t_date, "Credit Interest", t_amt, t_bal)
                acc.transactions.append(interest_transaction)
                db.save_new_transaction(acc.account_number, interest_transaction)
                db.update_account_state(acc)
        db.log_admin_action(self.current_user.account_number, "APPLY_INTEREST", "ALL_USERS", f"Rate: {rate}%")
        return f"Applied {rate}% annual interest to all eligible accounts."
    def get_audit_log(self):
        return db.get_audit_log()
    def get_interest_rate(self):
        return db.get_interest_rate()
    def set_interest_rate(self, rate):
        db.set_interest_rate(rate)
        db.log_admin_action(self.current_user.account_number, "SET_INTEREST_RATE", "SYSTEM", f"New rate: {rate}%")