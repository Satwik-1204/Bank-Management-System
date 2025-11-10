import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog
from backend_logic import BankSystem
import webbrowser
import os

class BankApp(ttk.Window):
    def __init__(self, bank_system):
        super().__init__(themename="litera")
        self.bank_system = bank_system
        self.title("Bank Management System")
        self.geometry("800x600")
        self.container = ttk.Frame(self, padding=10)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for F in (LoginScreen, UserDashboardScreen, AdminDashboardScreen, CreateAccountScreen):
            frame = F(parent=self.container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame("LoginScreen")
    def show_frame(self, page_name, data=None):
        frame = self.frames[page_name]
        if hasattr(frame, "on_show"):
            frame.on_show(data)
        frame.tkraise()
    def handle_login(self, acc_number, password):
        status, account, alert = self.bank_system.login(acc_number, password)
        if account:
            if alert: messagebox.showwarning("Alert", alert)
            if account.role == 'admin': self.show_frame("AdminDashboardScreen")
            else: self.show_frame("UserDashboardScreen")
        else:
            messagebox.showerror("Login Failed", status)
        
    def handle_logout(self):
        self.bank_system.logout()
        self.show_frame("LoginScreen")
    def handle_deposit(self, amount):
        status = self.bank_system.deposit(amount)
        messagebox.showinfo("Deposit Status", status)
        self.frames["UserDashboardScreen"].on_show()
    def handle_withdraw(self, amount):
        status = self.bank_system.withdraw(amount)
        messagebox.showinfo("Withdrawal Status", status)
        self.frames["UserDashboardScreen"].on_show()
    def handle_transfer(self, to_acc, amount):
        status = self.bank_system.transfer_funds(to_acc, amount)
        messagebox.showinfo("Transfer Status", status)
        self.frames["UserDashboardScreen"].on_show()
    def handle_update_name(self, new_name):
        status = self.bank_system.update_user_name(new_name)
        messagebox.showinfo("Update Status", status)
        self.frames["UserDashboardScreen"].on_show()
    def handle_update_password(self, old_p, new_p):
        status = self.bank_system.update_user_password(old_p, new_p)
        messagebox.showinfo("Update Status", status)
    def handle_admin_delete_user(self, acc_to_delete):
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to permanently delete account {acc_to_delete}?"):
            status = self.bank_system.admin_delete_account(acc_to_delete)
            messagebox.showinfo("Delete Status", status)
            self.frames["AdminDashboardScreen"].on_show()
    def handle_admin_unlock_user(self, acc_to_unlock):
        status = self.bank_system.admin_unlock_account(acc_to_unlock)
        messagebox.showinfo("Unlock Status", status)
        self.frames["AdminDashboardScreen"].on_show()
    def handle_admin_apply_interest(self):
        if messagebox.askyesno("Confirm Interest Application", "Apply annual interest to all accounts? This cannot be undone."):
            status = self.bank_system.admin_apply_interest()
            messagebox.showinfo("Status", status)

class LoginScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=20)
        self.controller = controller
        self.columnconfigure(0, weight=1)
        ttk.Label(self, text="Bank Management System", font="-size 24 -weight bold").grid(row=0, column=0, pady=(20, 10))
        ttk.Label(self, text="Please log in to continue", font="-size 12").grid(row=1, column=0, pady=(0, 20))
        form_frame = ttk.Frame(self)
        form_frame.grid(row=2, column=0, pady=10)
        ttk.Label(form_frame, text="Account Number:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.acc_number_entry = ttk.Entry(form_frame, width=30)
        self.acc_number_entry.grid(row=1, column=0, padx=5, pady=5)
        ttk.Label(form_frame, text="Password:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.password_entry = ttk.Entry(form_frame, show="*", width=30)
        self.password_entry.grid(row=3, column=0, padx=5, pady=5)
        ttk.Button(self, text="Login", command=self.login_action, bootstyle="primary", width=20).grid(row=3, column=0, pady=20)
        ttk.Button(self, text="Create New Account", command=lambda: controller.show_frame("CreateAccountScreen"), bootstyle="link").grid(row=4, column=0)
    def login_action(self):
        self.controller.handle_login(self.acc_number_entry.get(), self.password_entry.get())
        self.password_entry.delete(0, 'end')

class CreateAccountScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=20)
        self.controller = controller
        self.columnconfigure(0, weight=1)
        ttk.Label(self, text="Create a New Account", font="-size 24 -weight bold").grid(row=0, column=0, pady=(20, 10))
        form_frame = ttk.Frame(self)
        form_frame.grid(row=1, column=0, pady=10)
        fields = ["Full Name:", "Account Number:", "Password:", "Initial Deposit:"]
        self.entries = {}
        for i, field in enumerate(fields):
            ttk.Label(form_frame, text=field).grid(row=i*2, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(form_frame, width=30)
            if field == "Password:": entry.config(show="*")
            entry.grid(row=i*2+1, column=0, padx=5, pady=2)
            self.entries[field] = entry
        ttk.Button(self, text="Create Account", command=self.create_action, bootstyle="success", width=20).grid(row=2, column=0, pady=20)
        ttk.Button(self, text="Back to Login", command=lambda: controller.show_frame("LoginScreen"), bootstyle="link").grid(row=3, column=0)
    def create_action(self):
        try:
            name = self.entries["Full Name:"].get()
            acc_number = self.entries["Account Number:"].get()
            password = self.entries["Password:"].get()
            balance = float(self.entries["Initial Deposit:"].get())
            status = self.controller.bank_system.create_account(name, acc_number, password, balance)
            messagebox.showinfo("Account Creation Status", status)
            if "successfully" in status: self.controller.show_frame("LoginScreen")
        except ValueError: messagebox.showerror("Error", "Initial Deposit must be a valid number.")

class UserDashboardScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=10)
        self.controller = controller
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=X, pady=(0,10))
        self.welcome_label = ttk.Label(header_frame, text="Welcome, User", font="-size 18")
        self.welcome_label.pack(side=LEFT)
        ttk.Button(header_frame, text="Logout", command=lambda: controller.handle_logout(), bootstyle="secondary-outline").pack(side=RIGHT)
        self.notebook = ttk.Notebook(self, bootstyle="primary")
        self.notebook.pack(expand=True, fill="both")
        self.summary_tab = ttk.Frame(self.notebook, padding=10)
        self.history_tab = ttk.Frame(self.notebook, padding=10)
        self.transfer_tab = ttk.Frame(self.notebook, padding=10)
        self.profile_tab = ttk.Frame(self.notebook, padding=10)
        self.utils_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.summary_tab, text="Summary")
        self.notebook.add(self.history_tab, text="Transaction History")
        self.notebook.add(self.transfer_tab, text="Transfer Funds")
        self.notebook.add(self.profile_tab, text="My Profile")
        self.notebook.add(self.utils_tab, text="Utilities")
        self._populate_tabs()
    def _populate_tabs(self):
        self.details_label = ttk.Label(self.summary_tab, text="", font="-family Courier -size 12", justify=LEFT)
        self.details_label.pack(pady=20, padx=20, anchor="w")
        btn_frame = ttk.Frame(self.summary_tab)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Deposit", command=self.deposit_popup, bootstyle="success").pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Withdraw", command=self.withdraw_popup, bootstyle="danger").pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Generate PDF", command=lambda: self.generate_report("PDF"), bootstyle="info-outline").pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Export CSV", command=lambda: self.generate_report("CSV"), bootstyle="info-outline").pack(side="left", padx=10)
        cols = ("Date", "Type", "Amount", "Balance")
        self.tree = ttk.Treeview(self.history_tab, columns=cols, show='headings', bootstyle="primary")
        for col in cols: self.tree.heading(col, text=col)
        self.tree.pack(expand=True, fill="both")
        ttk.Label(self.transfer_tab, text="Recipient Account No:").pack(pady=5)
        self.to_acc_entry = ttk.Entry(self.transfer_tab, width=30)
        self.to_acc_entry.pack(pady=5)
        ttk.Label(self.transfer_tab, text="Amount (INR):").pack(pady=5)
        self.transfer_amt_entry = ttk.Entry(self.transfer_tab, width=30)
        self.transfer_amt_entry.pack(pady=5)
        ttk.Button(self.transfer_tab, text="Submit Transfer", command=self.submit_transfer, bootstyle="primary").pack(pady=20)
        ttk.Button(self.profile_tab, text="Change Name", command=self.change_name_popup).pack(pady=10, fill=X, padx=50)
        ttk.Button(self.profile_tab, text="Change Password", command=self.change_password_popup).pack(pady=10, fill=X, padx=50)
        util_frame = ttk.Frame(self.utils_tab)
        util_frame.pack(pady=20)
        ttk.Label(util_frame, text="Loan EMI Calculator", font="-size 14").grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Label(util_frame, text="Principal Amount (INR):").grid(row=1, column=0, sticky="w", pady=5)
        self.principal_entry = ttk.Entry(util_frame)
        self.principal_entry.grid(row=1, column=1)
        ttk.Label(util_frame, text="Annual Interest Rate (%):").grid(row=2, column=0, sticky="w", pady=5)
        self.rate_entry = ttk.Entry(util_frame)
        self.rate_entry.grid(row=2, column=1)
        ttk.Label(util_frame, text="Loan Term (Years):").grid(row=3, column=0, sticky="w", pady=5)
        self.years_entry = ttk.Entry(util_frame)
        self.years_entry.grid(row=3, column=1)
        ttk.Button(util_frame, text="Calculate EMI", command=self.calculate_emi).grid(row=4, column=0, columnspan=2, pady=10)
        self.emi_result_label = ttk.Label(util_frame, text="", font="-size 12 -weight bold", bootstyle="success")
        self.emi_result_label.grid(row=5, column=0, columnspan=2)
    def on_show(self, data=None):
        acc = self.controller.bank_system.get_current_user_details()
        if not acc: return
        self.welcome_label.config(text=f"Welcome, {acc.name}")
        details = (f"Account Holder: {acc.name}\n"
                f"Account Number: {acc.account_number}\n"
                f"Current Balance: INR {acc.balance:.2f}")
        self.details_label.config(text=details)
        for i in self.tree.get_children(): self.tree.delete(i)
        for t in acc.transactions:
            self.tree.insert("", "end", values=(t[0].strftime('%Y-%m-%d %H:%M'), t[1], f"{t[2]:.2f}", f"{t[3]:.2f}"))
    def deposit_popup(self):
        amount = simpledialog.askfloat("Deposit", "Enter amount:", parent=self)
        if amount: self.controller.handle_deposit(amount)
    def withdraw_popup(self):
        amount = simpledialog.askfloat("Withdraw", "Enter amount:", parent=self)
        if amount: self.controller.handle_withdraw(amount)
    def submit_transfer(self):
        to_acc = self.to_acc_entry.get()
        try:
            amount = float(self.transfer_amt_entry.get())
            self.controller.handle_transfer(to_acc, amount)
            self.to_acc_entry.delete(0, 'end')
            self.transfer_amt_entry.delete(0, 'end')
        except ValueError: messagebox.showerror("Error", "Amount must be a number.")
    def change_name_popup(self):
        new_name = simpledialog.askstring("Change Name", "Enter new name:", parent=self)
        if new_name: self.controller.handle_update_name(new_name)
    def change_password_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Change Password")
        ttk.Label(popup, text="Current Password:", padding=5).pack()
        old_p = ttk.Entry(popup, show="*", width=30); old_p.pack(pady=5, padx=10)
        ttk.Label(popup, text="New Password:", padding=5).pack()
        new_p = ttk.Entry(popup, show="*", width=30); new_p.pack(pady=5, padx=10)
        def submit():
            self.controller.handle_update_password(old_p.get(), new_p.get())
            popup.destroy()
        ttk.Button(popup, text="Submit", command=submit, bootstyle="primary").pack(pady=10)
    def generate_report(self, report_type):
        acc = self.controller.bank_system.get_current_user_details()
        if not acc: return
        if report_type == "PDF":
            file_path = acc.generate_statement()
            messagebox.showinfo("Success", f"Generated {file_path}")
            webbrowser.open(os.path.abspath(file_path))
        elif report_type == "CSV":
            file_path = acc.export_to_csv()
            messagebox.showinfo("Success", f"Generated {file_path}")
    def calculate_emi(self):
        try:
            p = float(self.principal_entry.get())
            r = float(self.rate_entry.get())
            y = int(self.years_entry.get())
            result = self.controller.bank_system.calculate_loan_emi(p, r, y)
            self.emi_result_label.config(text=result)
        except (ValueError, TypeError): messagebox.showerror("Error", "All fields must be valid numbers.")

class AdminDashboardScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=10)
        self.controller = controller
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=X, pady=(0,10))
        ttk.Label(header_frame, text="Administrator Dashboard", font="-size 18").pack(side=LEFT)
        ttk.Button(header_frame, text="Logout", command=lambda: controller.handle_logout(), bootstyle="secondary-outline").pack(side=RIGHT)
        self.notebook = ttk.Notebook(self, bootstyle="primary")
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")
        self.manage_tab = ttk.Frame(self.notebook, padding=10)
        self.financials_tab = ttk.Frame(self.notebook, padding=10)
        self.audit_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.manage_tab, text="User Management")
        self.notebook.add(self.financials_tab, text="System Financials")
        self.notebook.add(self.audit_tab, text="Audit Log")
        self._populate_manage_tab()
        self._populate_financials_tab()
        self._populate_audit_tab()
    def on_show(self, data=None):
        """Called whenever the frame is raised to the top."""
        self._update_manage_tab()
        self._update_financials_tab()
        self._update_audit_tab()
    def _populate_manage_tab(self):
        cols = ("Account No", "Name", "Balance", "Status")
        self.user_tree = ttk.Treeview(self.manage_tab, columns=cols, show='headings', bootstyle="primary")
        for col in cols: self.user_tree.heading(col, text=col)
        self.user_tree.pack(expand=True, fill="both")
        btn_frame = ttk.Frame(self.manage_tab)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Unlock Selected User", command=self._unlock_selected, bootstyle="warning").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete Selected User", command=self._delete_selected, bootstyle="danger").pack(side="left", padx=5)
    def _populate_financials_tab(self):
        rate_frame = ttk.Frame(self.financials_tab)
        rate_frame.pack(pady=20, padx=20)
        ttk.Label(rate_frame, text="Current Annual Interest Rate:", font="-size 12").pack(side="left", padx=10)
        self.rate_label = ttk.Label(rate_frame, text="", font="-size 12 -weight bold", bootstyle="info")
        self.rate_label.pack(side="left")
        ttk.Button(self.financials_tab, text="Update Interest Rate", command=self._update_rate_popup, bootstyle="secondary").pack(pady=10)
        ttk.Button(self.financials_tab, text="Apply Annual Interest to All Accounts", command=lambda: self.controller.handle_admin_apply_interest(), bootstyle="primary").pack(pady=20)
    def _populate_audit_tab(self):
        cols = ("Timestamp", "Admin", "Action", "Target", "Details")
        self.audit_tree = ttk.Treeview(self.audit_tab, columns=cols, show='headings', bootstyle="info")
        for col in cols:
            self.audit_tree.column(col, width=120)
            self.audit_tree.heading(col, text=col)
        self.audit_tree.pack(expand=True, fill="both")
    def _update_manage_tab(self):
        for i in self.user_tree.get_children(): self.user_tree.delete(i)
        users = self.controller.bank_system.admin_get_all_users_report()
        for u in users:
            if u.role != 'admin':
                status = "Locked" if u.is_locked else "Active"
                self.user_tree.insert("", "end", values=(u.account_number, u.name, f"{u.balance:.2f}", status))
    def _update_financials_tab(self):
        rate = self.controller.bank_system.get_interest_rate()
        self.rate_label.config(text=f"{rate}%")
    def _update_audit_tab(self):
        for i in self.audit_tree.get_children(): self.audit_tree.delete(i)
        logs = self.controller.bank_system.get_audit_log()
        for log in logs:
            self.audit_tree.insert("", "end", values=log)
    def _get_selected_account(self):
        selected_item = self.user_tree.focus()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a user from the list first.", parent=self)
            return None
        item_details = self.user_tree.item(selected_item)
        account_number = str(item_details['values'][0])
        return account_number
    def _unlock_selected(self):
        acc_num = self._get_selected_account()
        if acc_num: self.controller.handle_admin_unlock_user(acc_num)
    def _delete_selected(self):
        acc_num = self._get_selected_account()
        if acc_num: self.controller.handle_admin_delete_user(acc_num)
    def _update_rate_popup(self):
        new_rate = simpledialog.askfloat("Update Rate", "Enter new annual interest rate (%):", parent=self)
        if new_rate is not None and new_rate > 0:
            self.controller.bank_system.set_interest_rate(new_rate)
            self._update_financials_tab()

if __name__ == "__main__":
    bank_system = BankSystem()
    app = BankApp(bank_system)
    app.mainloop()