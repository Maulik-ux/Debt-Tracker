from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_connection
from models import EqualSplit, ByAmountSplit, ByPercentageSplit
from datetime import datetime, date
from config import Config

expense_bp = Blueprint('expenses', __name__, url_prefix='/expenses')

@expense_bp.route('/')
def list_expenses():
    if 'user_id' not in session:
        return redirect(url_for('auth.landing'))

    user_id = session['user_id']
    conn = get_connection()
    cursor = conn.cursor()

    # Query all expenses in groups user belongs to
    cursor.execute("""
        SELECT e.*, g.group_name, u.username as payer_name
        FROM expenses e
        JOIN expense_groups g ON e.group_id = g.group_id
        JOIN group_members gm ON g.group_id = gm.group_id
        JOIN users u ON e.paid_by = u.user_id
        WHERE gm.user_id = ?
        ORDER BY e.created_at DESC
    """, (user_id,))
    expense_rows = cursor.fetchall()

    today = date.today()
    activity_items = []

    for exp in expense_rows:
        eid = exp['expense_id']
        cursor.execute("""
            SELECT d.*, u_deb.username as debtor_name, u_cred.username as creditor_name
            FROM debts d
            JOIN users u_deb ON d.debtor_id = u_deb.user_id
            JOIN users u_cred ON d.creditor_id = u_cred.user_id
            WHERE d.expense_id = ?
        """, (eid,))
        debts = cursor.fetchall()

        exp_date = datetime.strptime(exp['expense_date'], '%Y-%m-%d').date()
        days_ago = (today - exp_date).days

        # Status check
        has_active = any(d['status'] == 'ACTIVE' for d in debts)
        if has_active and days_ago > Config.OVERDUE_DAYS:
            badge_status = 'OVERDUE'
        elif has_active:
            badge_status = 'ACTIVE'
        else:
            badge_status = 'SETTLED'

        activity_items.append({
            'expense': exp,
            'debts': debts,
            'days_ago': days_ago,
            'status': badge_status,
            'can_edit': (exp['paid_by'] == user_id)
        })

    conn.close()
    return render_template('expenses_view.html', activity=activity_items, user_id=user_id)

@expense_bp.route('/add', methods=['GET', 'POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('auth.landing'))

    user_id = session['user_id']
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        group_id = int(request.form.get('group_id'))
        description = request.form.get('description', 'Expense').strip()
        total_amount = float(request.form.get('amount', 0.0))
        category = request.form.get('category', 'Other')
        paid_by = int(request.form.get('paid_by'))
        expense_date = request.form.get('expense_date') or date.today().isoformat()
        split_type = request.form.get('split_type', 'Equally')

        split_members = [int(mid) for mid in request.form.getlist('split_members')]

        try:
            if total_amount <= 0:
                raise ValueError("Amount must be greater than 0.")
            if not split_members:
                raise ValueError("At least one person must be included in the split.")

            # Compute shares using OOP Split subclasses
            if split_type == 'Equally':
                splitter = EqualSplit(total_amount, split_members)
                shares = splitter.calculate_shares()
            elif split_type == 'By amount':
                amounts_input = {mid: request.form.get(f'amount_{mid}', 0) for mid in split_members}
                splitter = ByAmountSplit(total_amount, split_members)
                shares = splitter.calculate_shares(amounts_input)
            elif split_type == 'By percentage':
                pcts_input = {mid: request.form.get(f'pct_{mid}', 0) for mid in split_members}
                splitter = ByPercentageSplit(total_amount, split_members)
                shares = splitter.calculate_shares(pcts_input)

            # Insert expense row
            cursor.execute("""
                INSERT INTO expenses (group_id, paid_by, total_amount, description, category, split_type, expense_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (group_id, paid_by, total_amount, description, category, split_type, expense_date))
            expense_id = cursor.lastrowid

            # Insert splits and active debts
            for debtor_id, owed in shares.items():
                cursor.execute("""
                    INSERT INTO expense_splits (expense_id, user_id, amount_owed)
                    VALUES (?, ?, ?)
                """, (expense_id, debtor_id, owed))

                if debtor_id != paid_by and owed > 0:
                    cursor.execute("""
                        INSERT INTO debts (group_id, expense_id, debtor_id, creditor_id, amount, status)
                        VALUES (?, ?, ?, ?, ?, 'ACTIVE')
                    """, (group_id, expense_id, debtor_id, paid_by, owed))

            conn.commit()
            conn.close()
            flash("Expense added successfully!", "success")
            return redirect(url_for('expenses.list_expenses'))

        except Exception as e:
            flash(str(e), "error")

    # GET Request: Fetch user's groups
    cursor.execute("""
        SELECT g.group_id, g.group_name 
        FROM expense_groups g
        JOIN group_members gm ON g.group_id = gm.group_id
        WHERE gm.user_id = ?
    """, (user_id,))
    groups = cursor.fetchall()

    # Determine currently selected group
    selected_gid = request.args.get('selected_group_id', type=int) or (groups[0]['group_id'] if groups else None)
    
    current_members = []
    current_group_name = ""
    
    if selected_gid:
        cursor.execute("SELECT group_name FROM expense_groups WHERE group_id = ?", (selected_gid,))
        g_row = cursor.fetchone()
        if g_row:
            current_group_name = g_row['group_name']

        cursor.execute("""
            SELECT u.user_id, u.username 
            FROM users u 
            JOIN group_members gm ON u.user_id = gm.user_id 
            WHERE gm.group_id = ?
        """, (selected_gid,))
        current_members = cursor.fetchall()

    conn.close()

    return render_template(
        'expenses_form.html',
        groups=groups,
        current_group_id=selected_gid,
        current_group_name=current_group_name,
        current_members=current_members,
        today=date.today().isoformat()
    )

@expense_bp.route('/settle/<int:debt_id>', methods=['POST'])
def settle_debt(debt_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.landing'))

    user_id = session['user_id']
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM debts WHERE debt_id = ?", (debt_id,))
    debt = cursor.fetchone()

    if debt and debt['creditor_id'] == user_id:
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("UPDATE debts SET status = 'SETTLED', settled_at = ? WHERE debt_id = ?", (now_str, debt_id))
        conn.commit()
        flash("Debt marked as settled!", "success")

    conn.close()
    return redirect(url_for('expenses.list_expenses'))

@expense_bp.route('/delete/<int:expense_id>', methods=['GET', 'POST'])
def delete_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.landing'))

    user_id = session['user_id']
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM expenses WHERE expense_id = ?", (expense_id,))
    exp = cursor.fetchone()

    if not exp or exp['paid_by'] != user_id:
        conn.close()
        flash("Unauthorized request.", "error")
        return redirect(url_for('expenses.list_expenses'))

    if request.method == 'POST':
        cursor.execute("DELETE FROM expenses WHERE expense_id = ?", (expense_id,))
        conn.commit()
        conn.close()
        flash("Expense deleted.", "success")
        return redirect(url_for('expenses.list_expenses'))

    conn.close()
    return render_template('confirm_delete.html', item_type='Expense', item_name=exp['description'])