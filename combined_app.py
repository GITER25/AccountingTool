# --- Enhanced Streamlit Accounting Tool with AI Chatbot ---
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Page Configuration
st.set_page_config(
    layout="wide", 
    page_title="Accounting Analysis Tool",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #2a5298;
        margin: 1rem 0;
        min-height: 120px;
        height: 120px;
        width: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-sizing: border-box;
    }
    .metric-card h3 {
        color: #2a5298;
        margin-bottom: 0.5rem;
        font-size: 1rem;
        font-weight: 600;
        line-height: 1.2;
    }
    .metric-card h2 {
        color: #1e3c72;
        margin: 0;
        font-size: 1.2rem;
        word-wrap: break-word;
        line-height: 1.4;
    }
    .equation-table {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .statement-header {
        background: #2a5298;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        text-align: center;
        margin: 1rem 0;
    }
    .ratio-positive {
        color: #28a745;
        font-weight: bold;
    }
    .ratio-negative {
        color: #dc3545;
        font-weight: bold;
    }
    .chatbot-container {
        background: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .transaction-form {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .account-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #2a5298;
    }
</style>
""", unsafe_allow_html=True)

# Constants
SAVE_FILE = "student_transactions.json"

# Initialize Session State
if "account_inputs" not in st.session_state:
    st.session_state.account_inputs = []

if "submitted_transactions" not in st.session_state:
    st.session_state.submitted_transactions = []

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

if "transaction_desc" not in st.session_state:
    st.session_state.transaction_desc = ""

if "clear_description" not in st.session_state:
    st.session_state.clear_description = False

if "pending_edit" not in st.session_state:
    st.session_state.pending_edit = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Save & Load Functions
def save_to_file():
    with open(SAVE_FILE, "w") as f:
        json.dump({
            "submitted_transactions": st.session_state.submitted_transactions
        }, f)

def load_from_file():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
            st.session_state.submitted_transactions = data.get("submitted_transactions", [])

# ---------- Apply pending edit ----------
if st.session_state.pending_edit is not None:
    entry = st.session_state.submitted_transactions[st.session_state.pending_edit]
    st.session_state.transaction_desc = entry.get("description", "")
    for acc in entry["accounts"]:
        acc["selected_account"] = acc["name"]
    st.session_state.account_inputs = entry["accounts"].copy()
    st.session_state.edit_index = st.session_state.pending_edit
    st.session_state.pending_edit = None
    st.rerun()

# ---------- Clear description ----------
if st.session_state.clear_description:
    st.session_state.transaction_desc = ""
    st.session_state.clear_description = False

# ---------- Known Accounts ----------
def get_known_accounts():
    account_dict = {}
    for entry in st.session_state.submitted_transactions:
        for acc in entry["accounts"]:
            account_dict[acc["name"]] = {
                "type": acc["type"],
                "sub": acc["sub"],
                "line_item": acc["line_item"]
            }
    return account_dict

known_accounts = get_known_accounts()
known_account_names = sorted(known_accounts.keys())

# ---------- Classification Options ----------
sub_classification_options = {
    "Asset": ["Non-Current Assets", "Current Assets"],
    "Liability": ["Non-Current Liabilities", "Current Liabilities"],
    "Equity": ["Capital", "Retained Earnings", "Incomes", "Expenses"]
}

line_item_options = {
    "Non-Current Assets": ["Property, Plant & Equipment", "Intangible Assets", "Long Term Investments", "Other Non Current Assets"],
    "Current Assets": ["Inventory", "Trade Receivables", "Cash and Cash Equivalents", "Other Current Assets"],
    "Current Liabilities": ["Trade Payables", "Short Term Borrowings", "Outstanding Expenses", "Short Term Provisions", "Advance from Customers", "Other Current Liabilities"],
    "Non-Current Liabilities": ["Borrowings", "Long Term Provisions", "Other Non Current Liabilities"],
    "Capital": ["Not Applicable"],
    "Retained Earnings": ["Not Applicable"],
    "Incomes": ["Revenue from Operations", "Other Incomes"],
    "Expenses": ["Material related Expenses", "Employee Compensation Expenses", "Depreciation & Amortization", "Finance Costs", "Other Expenses", "Tax Expenses"]
}

def show_dashboard():
    st.markdown("## 🏠 Dashboard")
    
    if not st.session_state.submitted_transactions:
        st.info("👋 Welcome! Start by adding transactions to see your financial dashboard.")
        return
    
    # Calculate key metrics
    total_assets = sum(acc["amount"] for txn in st.session_state.submitted_transactions 
                      for acc in txn["accounts"] if acc["type"] == "Asset")
    total_liabilities = sum(acc["amount"] for txn in st.session_state.submitted_transactions 
                          for acc in txn["accounts"] if acc["type"] == "Liability")
    total_equity = sum(acc["amount"] for txn in st.session_state.submitted_transactions 
                      for acc in txn["accounts"] if acc["type"] == "Equity")
    
    # Key Metrics Section
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Total Assets</h3>
            <h2>₹{total_assets:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Total Liabilities</h3>
            <h2>₹{total_liabilities:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Total Equity</h3>
            <h2>₹{total_equity:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        current_ratio = total_assets / total_liabilities if total_liabilities > 0 else float('inf')
        ratio_color = "ratio-positive" if current_ratio >= 1.5 else "ratio-negative"
        st.markdown(f"""
        <div class="metric-card">
            <h3>Current Ratio</h3>
            <h2 class="{ratio_color}">{current_ratio:.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts Section
    col1, col2 = st.columns(2)
    
    with col1:
        # Assets vs Liabilities Chart
        fig = go.Figure(data=[
            go.Bar(
                name='Assets',
                x=['Financial Position'],
                y=[total_assets],
                marker_color='#28a745'
            ),
            go.Bar(
                name='Liabilities',
                x=['Financial Position'],
                y=[total_liabilities],
                marker_color='#dc3545'
            )
        ])
        fig.update_layout(
            title="Assets vs Liabilities",
            barmode='group',
            height=400,
            showlegend=True,
            yaxis_title="Amount (₹)",
            margin=dict(t=30, b=0, l=0, r=0)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Transaction Trend
        if len(st.session_state.submitted_transactions) > 1:
            dates = []
            amounts = []
            running_total = 0
            
            for txn in st.session_state.submitted_transactions:
                dates.append(txn["description"])
                txn_amount = sum(acc["amount"] for acc in txn["accounts"] if acc["type"] in ["Asset", "Liability"])
                running_total += txn_amount
                amounts.append(running_total)
            
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=amounts,
                    mode='lines+markers',
                    name='Cumulative Amount',
                    line=dict(color='#2a5298', width=2),
                    marker=dict(size=8)
                )
            )
            fig.update_layout(
                title="Transaction Trend",
                height=400,
                showlegend=True,
                xaxis_title="Transaction",
                yaxis_title="Cumulative Amount (₹)",
                margin=dict(t=30, b=0, l=0, r=0)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent Transactions
    st.subheader("Recent Transactions")
    recent_txns = st.session_state.submitted_transactions[-5:]  # Show last 5 transactions
    for txn in recent_txns:
        with st.expander(f"📝 {txn['description']}"):
            for acc in txn["accounts"]:
                st.write(f"• {acc['name']}: ₹{acc['amount']:,.2f} ({acc['type']})")

def show_transaction_entry():
    st.markdown("## ➕ Transaction Entry")
    
    # Add Reset/Delete Transactions Button at the top
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🗑️ Reset All Transactions", type="secondary"):
            if st.session_state.submitted_transactions:
                if st.warning("⚠️ Are you sure you want to delete all transactions? Click again to confirm."):
                    st.session_state.submitted_transactions = []
                    if os.path.exists(SAVE_FILE):
                        os.remove(SAVE_FILE)
                    st.success("✅ All transactions have been deleted!")
                    st.rerun()
    
    with st.container():
        st.markdown('<div class="transaction-form">', unsafe_allow_html=True)
        
        # --- Fix for clearing transaction description input ---
        if st.session_state.get("clear_description", False):
            st.session_state["entry_transaction_desc"] = ""
            st.session_state.clear_description = False
        
        # Transaction Description
        st.subheader("Enter Transaction Details")
        transaction_desc = st.text_input("Transaction Description", key="entry_transaction_desc", label_visibility="visible", disabled=False)
        
        # Add Account Button
        if st.button("➕ Add Another Account", key="add_account_btn"):
            st.session_state.account_inputs.append({
                "selected_account": "Other (New Account)",
                "name": "",
                "type": "Asset",
                "sub": "Current Assets",
                "line_item": "",
                "amount": 0.0
            })
        
        # Render Account Inputs
        accounts_to_delete = []
        if st.session_state.account_inputs:
            st.subheader("Accounts Involved")
            
            for i, acc in enumerate(st.session_state.account_inputs):
                st.markdown(f'<div class="account-card">', unsafe_allow_html=True)
                st.markdown(f"**Account {i+1}**")
                
                col1, col2 = st.columns(2)
                with col1:
                    options = known_account_names + ["Other (New Account)"]
                    acc["selected_account"] = st.selectbox(
                        "Select Account",
                        options,
                        index=options.index(acc["selected_account"]) if acc["selected_account"] in options else len(options) - 1,
                        key=f"select_{i}"
                    )
                    
                    is_new = acc["selected_account"] == "Other (New Account)"
                    if is_new:
                        acc["name"] = st.text_input("New Account Name", value=acc["name"], key=f"name_{i}", label_visibility="visible", disabled=False)
                    else:
                        acc["name"] = acc["selected_account"]
                        acc.update(known_accounts[acc["name"]])
                
                with col2:
                    acc["type"] = st.selectbox(
                        "Account Type",
                        ["Asset", "Liability", "Equity"],
                        index=["Asset", "Liability", "Equity"].index(acc["type"]),
                        key=f"type_{i}",
                        disabled=not is_new
                    )
                    
                    sub_opts = sub_classification_options[acc["type"]]
                    acc["sub"] = st.selectbox(
                        "Sub-Classification",
                        sub_opts,
                        index=sub_opts.index(acc["sub"]) if acc["sub"] in sub_opts else 0,
                        key=f"sub_{i}",
                        disabled=not is_new
                    )
                    
                    line_opts = line_item_options[acc["sub"]]
                    if acc["sub"] in ["Capital", "Retained Earnings"]:
                        acc["line_item"] = "Not Applicable"
                        st.selectbox("Line Item Type", ["Not Applicable"], key=f"line_{i}", disabled=True)
                    else:
                        acc["line_item"] = st.selectbox(
                            "Line Item Type",
                            line_opts,
                            index=line_opts.index(acc["line_item"]) if acc["line_item"] in line_opts else 0,
                            key=f"line_{i}",
                            disabled=not is_new
                        )
                
                col3, col4 = st.columns([3, 1])
                with col3:
                    acc["amount"] = st.number_input(
                        "Amount",
                        value=acc["amount"],
                        key=f"amount_{i}",
                        format="%.2f"
                    )
                with col4:
                    if st.button("🗑️ Delete", key=f"delete_{i}"):
                        accounts_to_delete.append(i)
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Delete marked accounts
        for idx in sorted(accounts_to_delete, reverse=True):
            del st.session_state.account_inputs[idx]
            st.rerun()
        
        # Submit Transaction
        if st.button("💾 Submit Transaction", key="submit_transaction"):
            if transaction_desc.strip() and all(acc["name"].strip() and acc["amount"] != 0 for acc in st.session_state.account_inputs):
                new_entry = {"description": transaction_desc, "accounts": st.session_state.account_inputs.copy()}
                if st.session_state.edit_index is not None:
                    st.session_state.submitted_transactions[st.session_state.edit_index] = new_entry
                    st.session_state.edit_index = None
                else:
                    st.session_state.submitted_transactions.append(new_entry)
                st.session_state.account_inputs.clear()
                st.session_state.clear_description = True
                save_to_file()
                st.success("✅ Transaction added successfully!")
                st.rerun()
            else:
                st.warning("Please fill in all details and non-zero amounts.")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Add individual transaction delete buttons below the form
    if st.session_state.submitted_transactions:
        st.markdown("---")
        st.subheader("All Transactions")
        for idx, txn in enumerate(st.session_state.submitted_transactions):
            with st.expander(f"📝 {txn['description']}"):
                for acc in txn["accounts"]:
                    st.write(f"• {acc['name']}: ₹{acc['amount']:,.2f} ({acc['type']})")
                if st.button("Delete Transaction", key=f"delete_txn_{idx}"):
                    del st.session_state.submitted_transactions[idx]
                    save_to_file()
                    st.success("Transaction deleted successfully!")
                    st.rerun()

def show_accounting_equation():
    st.markdown("## 📋 Accounting Equation Table")
    
    if not st.session_state.submitted_transactions:
        st.info("No transactions recorded yet. Add transactions to see the accounting equation in action.")
        return

    # Define the columns for the table
    account_columns = [
        "Cash", "Inventory", "Equipment", "Receivable", "Other Assets",
        "Liabilities", "Capital", "Incomes", "Expenses"
    ]
    table_columns = ["No."] + account_columns + ["Description"]

    # Prepare the data for the table
    table_data = []
    running_totals = {col: 0 for col in account_columns}

    for idx, txn in enumerate(st.session_state.submitted_transactions):
        row = {col: 0 for col in account_columns}
        for acc in txn["accounts"]:
            # Map account names/types to columns
            if acc["name"].lower() == "cash":
                row["Cash"] += acc["amount"]
            elif acc["name"].lower() == "inventory":
                row["Inventory"] += acc["amount"]
            elif acc["name"].lower() == "equipment":
                row["Equipment"] += acc["amount"]
            elif acc["name"].lower() in ["receivable", "receivables"]:
                row["Receivable"] += acc["amount"]
            elif acc["type"] == "Asset" and acc["name"].lower() not in ["cash", "inventory", "equipment", "receivable", "receivables"]:
                row["Other Assets"] += acc["amount"]
            elif acc["type"] == "Liability":
                row["Liabilities"] += acc["amount"]
            elif acc["type"] == "Equity" and acc["sub"] == "Capital":
                row["Capital"] += acc["amount"]
            elif acc["type"] == "Equity" and acc["sub"] in ["Incomes", "Income"]:
                row["Incomes"] += acc["amount"]
            elif acc["type"] == "Equity" and acc["sub"] == "Expenses":
                row["Expenses"] += acc["amount"]
        # Update running totals
        for col in account_columns:
            running_totals[col] += row[col]
        table_data.append([
            idx + 1,
            *(row[col] if row[col] != 0 else "" for col in account_columns),
            txn["description"]
        ])

    # Add running totals row (not shown)
    # totals_row = ["Total"] + [running_totals[col] for col in account_columns] + [""]
    
    # Calculate equation check
    assets_total = running_totals["Cash"] + running_totals["Inventory"] + running_totals["Equipment"] + running_totals["Receivable"] + running_totals["Other Assets"]
    liabilities_total = running_totals["Liabilities"]
    equity_total = running_totals["Capital"] + running_totals["Incomes"] + running_totals["Expenses"]
    equation_balanced = abs(assets_total - (liabilities_total + equity_total)) < 0.01

    # Display as a dataframe
    df = pd.DataFrame(table_data, columns=table_columns)
    st.dataframe(df, use_container_width=True)

    # --- Add summary section for Assets, Liabilities, Equity (as before) ---
    st.markdown('<div class="equation-table">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="statement-header">ASSETS</div>', unsafe_allow_html=True)
        total_assets = 0
        for name in ["Cash", "Inventory", "Equipment", "Receivable", "Other Assets"]:
            amount = running_totals[name]
            st.write(f"• {name}: ₹{amount:,.2f}")
            total_assets += amount
        st.markdown(f"**Total Assets: ₹{total_assets:,.2f}**")
    with col2:
        st.markdown('<div class="statement-header">LIABILITIES</div>', unsafe_allow_html=True)
        total_liabilities = running_totals["Liabilities"]
        st.write(f"• Liabilities: ₹{total_liabilities:,.2f}")
        st.markdown(f"**Total Liabilities: ₹{total_liabilities:,.2f}**")
    with col3:
        st.markdown('<div class="statement-header">EQUITY</div>', unsafe_allow_html=True)
        total_equity = running_totals["Capital"] + running_totals["Incomes"] + running_totals["Expenses"]
        st.write(f"• Capital: ₹{running_totals['Capital']:,.2f}")
        st.write(f"• Incomes: ₹{running_totals['Incomes']:,.2f}")
        st.write(f"• Expenses: ₹{running_totals['Expenses']:,.2f}")
        st.markdown(f"**Total Equity: ₹{total_equity:,.2f}**")
    st.markdown('</div>', unsafe_allow_html=True)

    # Show balance check
    st.write(f"**Assets:** {assets_total:,.2f} | **Liabilities + Equity:** {liabilities_total + equity_total:,.2f}")
    if equation_balanced:
        st.success(f"✅ Equation Balanced! Assets (₹{assets_total:,.2f}) = Liabilities (₹{liabilities_total:,.2f}) + Equity (₹{equity_total:,.2f})")
    else:
        st.error(f"❌ Equation Imbalanced! Assets (₹{assets_total:,.2f}) ≠ Liabilities (₹{liabilities_total:,.2f}) + Equity (₹{equity_total:,.2f})")

def show_financial_statements():
    st.markdown("## 📊 Financial Statements")
    
    if not st.session_state.submitted_transactions:
        st.warning("No transactions available. Please add transactions first.")
        return

    # Create tabs for different statements
    bs_tab, is_tab, cf_tab = st.tabs(["Balance Sheet", "Income Statement", "Cash Flow Statement"])
    
    # Helper function to format currency
    def format_currency(amount):
        return f"₹{amount:,.2f}"
    
    # Calculate account totals
    account_totals = {}
    for txn in st.session_state.submitted_transactions:
        for acc in txn["accounts"]:
            key = (acc["type"], acc["sub"], acc["line_item"], acc["name"])
            if key not in account_totals:
                account_totals[key] = 0
            account_totals[key] += acc["amount"]
    
    # ---- Balance Sheet ----
    with bs_tab:
        st.markdown("### Balance Sheet")
        st.markdown("*As of current date*")
        
        # Assets
        st.markdown("#### Assets")
        total_assets = 0
        
        # Non-Current Assets
        st.markdown("**Non-Current Assets**")
        nca_total = 0
        for key, amount in account_totals.items():
            if key[0] == "Asset" and key[1] == "Non-Current Assets":
                st.write(f"{key[2]}: {format_currency(amount)}")
                nca_total += amount
        st.markdown(f"*Total Non-Current Assets: {format_currency(nca_total)}*")
        total_assets += nca_total
        
        # Current Assets
        st.markdown("**Current Assets**")
        ca_total = 0
        for key, amount in account_totals.items():
            if key[0] == "Asset" and key[1] == "Current Assets":
                st.write(f"{key[2]}: {format_currency(amount)}")
                ca_total += amount
        st.markdown(f"*Total Current Assets: {format_currency(ca_total)}*")
        total_assets += ca_total
        
        st.markdown(f"**Total Assets: {format_currency(total_assets)}**")
        st.markdown("---")
        
        # Liabilities and Equity
        st.markdown("#### Liabilities and Equity")
        
        # Non-Current Liabilities
        st.markdown("**Non-Current Liabilities**")
        ncl_total = 0
        for key, amount in account_totals.items():
            if key[0] == "Liability" and key[1] == "Non-Current Liabilities":
                st.write(f"{key[2]}: {format_currency(amount)}")
                ncl_total += amount
        st.markdown(f"*Total Non-Current Liabilities: {format_currency(ncl_total)}*")
        
        # Current Liabilities
        st.markdown("**Current Liabilities**")
        cl_total = 0
        for key, amount in account_totals.items():
            if key[0] == "Liability" and key[1] == "Current Liabilities":
                st.write(f"{key[2]}: {format_currency(amount)}")
                cl_total += amount
        st.markdown(f"*Total Current Liabilities: {format_currency(cl_total)}*")
        
        total_liabilities = ncl_total + cl_total
        st.markdown(f"**Total Liabilities: {format_currency(total_liabilities)}**")
        
        # Equity
        st.markdown("**Equity**")
        equity_total = 0
        retained_earnings = 0
        
        # Capital
        capital_total = 0
        for key, amount in account_totals.items():
            if key[0] == "Equity" and key[1] == "Capital":
                capital_total += amount
        st.write(f"Capital: {format_currency(capital_total)}")
        
        # Calculate Retained Earnings (Net Income)
        income_total = 0
        expense_total = 0
        for key, amount in account_totals.items():
            if key[0] == "Equity":
                if key[1] == "Incomes":
                    income_total += amount
                elif key[1] == "Expenses":
                    expense_total += abs(amount)
        
        retained_earnings = income_total - expense_total
        st.write(f"Retained Earnings: {format_currency(retained_earnings)}")
        
        equity_total = capital_total + retained_earnings
        st.markdown(f"**Total Equity: {format_currency(equity_total)}**")
        
        st.markdown(f"**Total Liabilities and Equity: {format_currency(total_liabilities + equity_total)}**")
        
        # Balance check
        if abs(total_assets - (total_liabilities + equity_total)) < 0.01:
            st.success("✅ Balance Sheet is balanced!")
        else:
            st.error("❌ Balance Sheet is not balanced!")
    
    # ---- Income Statement ----
    with is_tab:
        st.markdown("### Income Statement")
        st.markdown("*For the current period*")
        
        # Revenue
        st.markdown("#### Revenue")
        revenue_total = 0
        for key, amount in account_totals.items():
            if key[0] == "Equity" and key[1] == "Incomes":
                st.write(f"{key[2]}: {format_currency(amount)}")
                revenue_total += amount
        st.markdown(f"**Total Revenue: {format_currency(revenue_total)}**")
        
        # Expenses
        st.markdown("#### Expenses")
        total_expenses = 0
        for key, amount in account_totals.items():
            if key[0] == "Equity" and key[1] == "Expenses":
                st.write(f"{key[2]}: {format_currency(abs(amount))}")
                total_expenses += abs(amount)
        st.markdown(f"**Total Expenses: {format_currency(total_expenses)}**")
        
        # Net Income
        net_income = revenue_total - total_expenses
        st.markdown("#### Net Income")
        st.markdown(f"**Net Income: {format_currency(net_income)}**")
    
    # ---- Cash Flow Statement ----
    with cf_tab:
        st.markdown("### Cash Flow Statement")
        st.markdown("*For the current period*")
        
        # Operating Activities
        st.markdown("#### Operating Activities")
        operating_cash_flow = 0
        
        # Net Income
        st.write(f"Net Income: {format_currency(net_income)}")
        operating_cash_flow += net_income
        
        # Adjustments for non-cash items
        depreciation = 0
        for key, amount in account_totals.items():
            if key[0] == "Equity" and key[2] == "Depreciation & Amortization":
                depreciation = abs(amount)
        st.write(f"Depreciation and Amortization: {format_currency(depreciation)}")
        operating_cash_flow += depreciation
        
        # Changes in working capital
        working_capital_changes = 0
        for key, amount in account_totals.items():
            if key[0] == "Asset" and key[1] == "Current Assets" and key[2] != "Cash and Cash Equivalents":
                working_capital_changes -= amount
            elif key[0] == "Liability" and key[1] == "Current Liabilities":
                working_capital_changes += amount
        st.write(f"Changes in Working Capital: {format_currency(working_capital_changes)}")
        operating_cash_flow += working_capital_changes
        
        st.markdown(f"**Net Cash from Operating Activities: {format_currency(operating_cash_flow)}**")
        
        # Investing Activities
        st.markdown("#### Investing Activities")
        investing_cash_flow = 0
        for key, amount in account_totals.items():
            if key[0] == "Asset" and key[1] == "Non-Current Assets":
                investing_cash_flow -= amount
                st.write(f"Purchase of {key[2]}: {format_currency(-amount)}")
        st.markdown(f"**Net Cash from Investing Activities: {format_currency(investing_cash_flow)}**")
        
        # Financing Activities
        st.markdown("#### Financing Activities")
        financing_cash_flow = 0
        for key, amount in account_totals.items():
            if key[0] == "Liability" and key[1] == "Non-Current Liabilities":
                financing_cash_flow += amount
                st.write(f"Proceeds from {key[2]}: {format_currency(amount)}")
            elif key[0] == "Equity" and key[1] == "Capital":
                financing_cash_flow += amount
                st.write(f"Capital Contribution: {format_currency(amount)}")
        st.markdown(f"**Net Cash from Financing Activities: {format_currency(financing_cash_flow)}**")
        
        # Net Change in Cash
        net_change_in_cash = operating_cash_flow + investing_cash_flow + financing_cash_flow
        st.markdown("#### Net Change in Cash")
        st.markdown(f"**Net Increase (Decrease) in Cash: {format_currency(net_change_in_cash)}**")

def show_ratio_analysis():
    st.markdown("## 📈 Ratio Analysis")
    
    if not st.session_state.submitted_transactions:
        st.warning("No transactions available for ratio analysis.")
        return
    
    # Calculate totals from transactions
    total_assets = 0
    total_liabilities = 0
    total_equity = 0
    current_assets = 0
    current_liabilities = 0
    inventory = 0
    net_income = 0
    revenue = 0
    total_expenses = 0
    
    for txn in st.session_state.submitted_transactions:
        for acc in txn["accounts"]:
            amount = acc["amount"]
            
            if acc["type"] == "Asset":
                total_assets += amount
                if acc["sub"] == "Current Assets":
                    current_assets += amount
                    if acc["line_item"] == "Inventory":
                        inventory += amount
            
            elif acc["type"] == "Liability":
                total_liabilities += amount
                if acc["sub"] == "Current Liabilities":
                    current_liabilities += amount
            
            elif acc["type"] == "Equity":
                if acc["sub"] == "Incomes":
                    revenue += amount
                elif acc["sub"] == "Expenses":
                    total_expenses += abs(amount)
                else:
                    total_equity += amount
    
    net_income = revenue - total_expenses
    
    # Create ratio categories
    ratios = {
        "Liquidity Ratios": {
            "Current Ratio": {
                "value": current_assets / current_liabilities if current_liabilities else float('inf'),
                "formula": "Current Assets / Current Liabilities",
                "interpretation": {
                    "poor": "< 1.0",
                    "good": "1.0 - 1.5",
                    "excellent": "> 1.5"
                }
            },
            "Quick Ratio": {
                "value": (current_assets - inventory) / current_liabilities if current_liabilities else float('inf'),
                "formula": "(Current Assets - Inventory) / Current Liabilities",
                "interpretation": {
                    "poor": "< 1.0",
                    "good": "1.0 - 1.5",
                    "excellent": "> 1.5"
                }
            }
        },
        "Solvency Ratios": {
            "Debt to Equity": {
                "value": total_liabilities / total_equity if total_equity else float('inf'),
                "formula": "Total Liabilities / Total Equity",
                "interpretation": {
                    "excellent": "< 1.0",
                    "good": "1.0 - 2.0",
                    "poor": "> 2.0"
                }
            },
            "Debt to Assets": {
                "value": total_liabilities / total_assets if total_assets else 0,
                "formula": "Total Liabilities / Total Assets",
                "interpretation": {
                    "excellent": "< 0.4",
                    "good": "0.4 - 0.6",
                    "poor": "> 0.6"
                }
            }
        },
        "Profitability Ratios": {
            "Net Profit Margin": {
                "value": (net_income / revenue * 100) if revenue else 0,
                "formula": "(Net Income / Revenue) × 100",
                "interpretation": {
                    "poor": "< 5%",
                    "good": "5% - 10%",
                    "excellent": "> 10%"
                }
            },
            "Return on Assets": {
                "value": (net_income / total_assets * 100) if total_assets else 0,
                "formula": "(Net Income / Total Assets) × 100",
                "interpretation": {
                    "poor": "< 5%",
                    "good": "5% - 10%",
                    "excellent": "> 10%"
                }
            },
            "Return on Equity": {
                "value": (net_income / total_equity * 100) if total_equity else 0,
                "formula": "(Net Income / Total Equity) × 100",
                "interpretation": {
                    "poor": "< 10%",
                    "good": "10% - 15%",
                    "excellent": "> 15%"
                }
            }
        }
    }
    
    # Display ratios in an organized manner
    for category, category_ratios in ratios.items():
        st.markdown(f"### {category}")
        cols = st.columns(len(category_ratios))
        
        for i, (ratio_name, ratio_data) in enumerate(category_ratios.items()):
            with cols[i]:
                value = ratio_data["value"]
                if isinstance(value, float) and value != float('inf'):
                    if "Margin" in ratio_name or "Return" in ratio_name:
                        formatted_value = f"{value:.1f}%"
                    else:
                        formatted_value = f"{value:.2f}"
                else:
                    formatted_value = "∞" if value == float('inf') else "N/A"
                
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{ratio_name}</h3>
                    <h2>{formatted_value}</h2>
                    <p><em>Formula:</em> {ratio_data['formula']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("**Interpretation:**")
                for level, threshold in ratio_data["interpretation"].items():
                    st.markdown(f"- {level.title()}: {threshold}")

def show_learning_hub():
    st.markdown("## 🎓 Learning Hub")
    
    tab1, tab2, tab3 = st.tabs(["📚 Core Concepts", "🔄 Transaction Analysis", "📊 Statement Preparation"])
    
    with tab1:
        st.markdown("""
        ### The Accounting Equation
        
        The fundamental accounting equation is:
        ```
        Assets = Liabilities + Equity
        ```
        
        - **Assets**: Resources owned by the business
        - **Liabilities**: Debts and obligations
        - **Equity**: Owner's claim on assets
        
        ### Double-Entry System
        
        Every transaction affects at least two accounts:
        - One account is debited
        - Another account is credited
        
        ### Types of Accounts
        
        1. **Asset Accounts**
           - Cash
           - Accounts Receivable
           - Inventory
           - Equipment
        
        2. **Liability Accounts**
           - Accounts Payable
           - Loans Payable
           - Notes Payable
        
        3. **Equity Accounts**
           - Owner's Capital
           - Retained Earnings
           - Revenue
           - Expenses
        """)
    
    with tab2:
        st.markdown("""
        ### Transaction Analysis Framework
        
        1. **Identify the Transaction**
           - What business event occurred?
           - What accounts are affected?
        
        2. **Analyze Account Changes**
           - Which accounts increase?
           - Which accounts decrease?
        
        3. **Record the Transaction**
           - Enter the date
           - Enter the description
           - Record the amounts
        
        ### Example Transactions
        
        1. **Owner Invests Cash**
           - Cash (Asset) increases
           - Owner's Capital (Equity) increases
        
        2. **Purchase Equipment on Credit**
           - Equipment (Asset) increases
           - Accounts Payable (Liability) increases
        
        3. **Pay Monthly Rent**
           - Cash (Asset) decreases
           - Rent Expense (Equity) increases
        """)
    
    with tab3:
        st.markdown("""
        ### Financial Statement Preparation
        
        1. **Balance Sheet**
           - Lists all assets, liabilities, and equity
           - Must balance: Assets = Liabilities + Equity
           - Shows financial position at a point in time
        
        2. **Income Statement**
           - Shows revenues and expenses
           - Calculates net income or loss
           - Covers a period of time
        
        ### Tips for Statement Preparation
        
        1. **Organize Accounts**
           - Group similar accounts together
           - Use proper classifications
        
        2. **Check for Accuracy**
           - Verify all transactions are included
           - Ensure the accounting equation balances
           - Cross-reference between statements
        
        3. **Present Clearly**
           - Use consistent formatting
           - Include proper headings
           - Show subtotals and totals
        """)

def show_ai_assistant():
    st.markdown("## 🤖 AI Assistant")
    st.markdown("### Your Personal Accounting Guide")
    
    # Display chat history
    for message in st.session_state.chat_history:
        st.markdown(f"**You:** {message[0]}")
        st.markdown(f"**Assistant:** {message[1]}")
    
    # Chat input
    user_input = st.text_input("Ask me anything about accounting:", key="chat_input")
    
    if st.button("Send"):
        if user_input:
            # Add basic responses for common questions
            response = "I understand you're asking about accounting concepts. Could you be more specific about what you'd like to learn?"
            
            if "accounting equation" in user_input.lower():
                response = "The accounting equation (Assets = Liabilities + Equity) is the foundation of double-entry accounting. It shows that a company's assets are financed by either debt (liabilities) or owner's investment (equity)."
            elif "balance sheet" in user_input.lower():
                response = "A balance sheet shows a company's financial position at a specific point in time. It lists all assets, liabilities, and equity, following the accounting equation: Assets = Liabilities + Equity."
            elif "income statement" in user_input.lower():
                response = "An income statement shows a company's financial performance over a period. It lists revenues (income) and expenses, with the difference being net income or loss."
            
            st.session_state.chat_history.append((user_input, response))
            st.rerun()

def show_export_section():
    st.markdown("## 📤 Export Data")
    
    if not st.session_state.submitted_transactions:
        st.warning("No data available for export.")
        return
    
    # Prepare transaction data for export
    data = []
    for txn in st.session_state.submitted_transactions:
        for acc in txn["accounts"]:
            data.append({
                "Description": txn["description"],
                "Account Type": acc["type"],
                "Account Name": acc["name"],
                "Amount": acc["amount"]
            })
    
    df = pd.DataFrame(data)
    
    # Excel export
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Transactions", index=False)
    
    st.download_button(
        label="📥 Download Excel Report",
        data=excel_buffer.getvalue(),
        file_name=f"accounting_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def main():
    # Load saved transactions
    load_from_file()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>Accounting Analysis Tool</h1>
        <p>Advanced Financial Management System Based on Accounting Equation Methodology</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar Navigation
    with st.sidebar:
        st.markdown("### 📊 Navigation")
        
        selected_tab = st.selectbox(
            "Choose Section:",
            ["🏠 Dashboard", "➕ Transaction Entry", "📋 Accounting Equation", 
             "📊 Financial Statements", "📈 Ratio Analysis", "🎓 Learning Hub", 
             "🤖 AI Assistant", "📤 Export Data"]
        )
    
    # Main Content Based on Selection
    if selected_tab == "🏠 Dashboard":
        show_dashboard()
    elif selected_tab == "➕ Transaction Entry":
        show_transaction_entry()
    elif selected_tab == "📋 Accounting Equation":
        show_accounting_equation()
    elif selected_tab == "📊 Financial Statements":
        show_financial_statements()
    elif selected_tab == "📈 Ratio Analysis":
        show_ratio_analysis()
    elif selected_tab == "🎓 Learning Hub":
        show_learning_hub()
    elif selected_tab == "🤖 AI Assistant":
        show_ai_assistant()
    elif selected_tab == "📤 Export Data":
        show_export_section()

if __name__ == "__main__":
    main() 