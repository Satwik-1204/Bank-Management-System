import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import csv
import bcrypt

def is_strong_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit."
    return True, "Password is strong."

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

class Account:
    MAX_FAILED_ATTEMPTS = 3
    def __init__(self, name, account_number, balance, password_hash, role='user', failed_attempts=0, is_locked=0):
        self.name = name
        self.account_number = account_number
        self.balance = float(balance)
        self.password_hash = password_hash
        self.role = role
        self.failed_attempts = int(failed_attempts)
        self.is_locked = bool(is_locked)
        self.transactions = []
    def verify_password(self, password):
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())
    def deposit(self, value):
        if value <= 0:
            print("Deposit amount must be positive!")
            return None
        self.balance += value
        transaction = (datetime.now(), "Deposit", value, self.balance)
        self.transactions.append(transaction)
        print(f"Deposited: {value:.2f}. New Balance: {self.balance:.2f}")
        return transaction
    def withdraw(self, value):
        if value <= 0:
            print("Withdrawal amount must be positive!")
            return None
        if value > self.balance:
            print("Balance Insufficient!")
            return None
        self.balance -= value
        transaction = (datetime.now(), "Withdrawal", value, self.balance)
        self.transactions.append(transaction)
        print(f"Withdrawn: {value:.2f}. New Balance: {self.balance:.2f}")
        return transaction
    def increment_failed_attempts(self):
        self.failed_attempts += 1
        if self.failed_attempts >= self.MAX_FAILED_ATTEMPTS:
            self.lock()
    def reset_failed_attempts(self):
        self.failed_attempts = 0
        self.unlock()
    def lock(self):
        self.is_locked = True
        print(f"Account {self.account_number} has been locked due to too many failed login attempts.")
    def unlock(self):
        self.is_locked = False
    def display(self):
        print(f"\n--- Account Details ---")
        print(f"Account Holder's Name: {self.name}")
        print(f"Account Number: {self.account_number}")
        print(f"Bank Balance: INR {self.balance:.2f}")
        print(f"Account Status: {'Locked' if self.is_locked else 'Active'}")
        print("-----------------------")
    def generate_statement(self):
        pdf_file = f"Bank_Statement_{self.account_number}.pdf"
        doc = SimpleDocTemplate(pdf_file, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        elements.append(Paragraph("Bank Statement", styles['Heading1']))
        elements.append(Paragraph(f"Account Holder's Name: {self.name}", styles['Normal']))
        elements.append(Paragraph(f"Account Number: {self.account_number}", styles['Normal']))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Paragraph("<br/><br/>", styles['Normal']))
        data = [["Date & Time", "Transaction Type", "Amount", "Balance"]]
        for t_date, t_type, t_amount, t_balance in self.transactions:
            data.append([
                t_date.strftime("%Y-%m-%d %H:%M:%S"),
                t_type,
                f"INR {t_amount:.2f}",
                f"INR {t_balance:.2f}"
            ])
        table = Table(data)
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        table.setStyle(style)
        for i, row in enumerate(self.transactions, start=1):
            if row[1] in ["Deposit", "Initial Deposit", "Transfer In"]:
                table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.lightgreen)]))
            elif row[1] in ["Withdrawal", "Transfer Out"]:
                table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.lightcoral)]))
        elements.append(table)
        doc.build(elements)
        return pdf_file
    def export_to_csv(self):
        csv_file = f"Transactions_{self.account_number}.csv"
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Date & Time", "Transaction Type", "Amount", "Balance"])
            for t_date, t_type, t_amount, t_balance in self.transactions:
                writer.writerow([
                    t_date.strftime("%Y-%m-%d %H:%M:%S"),
                    t_type,
                    t_amount,
                    t_balance
                ])
        return csv_file