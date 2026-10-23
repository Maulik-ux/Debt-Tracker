from flask import Blueprint, render_template, session, redirect, url_for
from database import get_connection
from utils.history_stack import get_recent_activity_top_3
from utils.search_sort import selection_sort_by_amount
from datetime import datetime
from config import Config

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.landing'))

    user_id = session['user_id']
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Fetch active debts involving logged in user
    cursor.execute("""
        SELECT d.*, u_cred.username as creditor_name, u_deb.username as debtor_name, g.group_name
        FROM debts d
        JOIN users u_cred ON d.creditor_id = u_cred.user_id
        JOIN users u_deb ON d.debtor_id = u_deb.user_id
        JOIN expense_groups g ON d.group_id = g.group_id
        WHERE (d.debtor_id = ? OR d.creditor_id = ?) AND d.status = 'ACTIVE'
    """, (user_id, user_id))
    active_debts = cursor.fetchall()

    you_owe_total = 0.0
    you_are_owed_total = 0.0
    active_owe_count = 0
    active_owed_count = 0

    # Person-by-person breakdown dictionary (Splitwise style)
    person_balances = {}

    for debt in active_debts:
        amt = debt['amount']
        if debt['debtor_id'] == user_id:
            you_owe_total += amt
            active_owe_count += 1
            other_id = debt['creditor_id']
            other_name = debt['creditor_name']
            person_balances[other_name] = person_balances.get(other_name, 0.0) - amt
        elif debt['creditor_id'] == user_id:
            you_are_owed_total += amt
            active_owed_count += 1
            other_id = debt['debtor_id']
            other_name = debt['debtor_name']
            person_balances[other_name] = person_balances.get(other_name, 0.0) + amt

    net_balance = round(you_are_owed_total - you_owe_total, 2)

    # Convert person balances to formatted list
    person_debt_list = []
    for name, bal in person_balances.items():
        person_debt_list.append({
            'name': name,
            'amount': abs(round(bal, 2)),
            'type': 'OWES_YOU' if bal > 0 else ('YOU_OWE' if bal < 0 else 'SETTLED')
        })

    # 2. Count transactions this month
    current_month = datetime.now().strftime('%Y-%m')
    cursor.execute("""
        SELECT COUNT(*) as month_count 
        FROM expenses e
        JOIN group_members gm ON e.group_id = gm.group_id
        WHERE gm.user_id = ? AND strftime('%Y-%m', e.expense_date) = ?
    """, (user_id, current_month))
    month_tx_count = cursor.fetchone()['month_count']

    # 3. Fetch user groups and compute net balance per group
    cursor.execute("""
        SELECT g.group_id, g.group_name,
               (SELECT COUNT(*) FROM group_members WHERE group_id = g.group_id) as member_count
        FROM expense_groups g
        JOIN group_members gm ON g.group_id = gm.group_id
        WHERE gm.user_id = ?
    """, (user_id,))
    user_groups = cursor.fetchall()

    group_balances_list = []
    for g in user_groups:
        gid = g['group_id']
        cursor.execute("""
            SELECT debtor_id, creditor_id, amount 
            FROM debts 
            WHERE group_id = ? AND status = 'ACTIVE' AND (debtor_id = ? OR creditor_id = ?)
        """, (gid, user_id, user_id))
        g_debts = cursor.fetchall()

        g_net = 0.0
        for d in g_debts:
            if d['creditor_id'] == user_id:
                g_net += d['amount']
            else:
                g_net -= d['amount']

        group_balances_list.append({
            'group_id': gid,
            'group_name': g['group_name'],
            'member_count': g['member_count'],
            'amount': round(g_net, 2)
        })

    sorted_group_balances = selection_sort_by_amount(group_balances_list, reverse=True)

    # 4. Fetch recent activity
    cursor.execute("""
        SELECT e.expense_id, e.description, e.total_amount, e.expense_date,
               g.group_name, u.username as payer_name, e.paid_by
        FROM expenses e
        JOIN expense_groups g ON e.group_id = g.group_id
        JOIN group_members gm ON g.group_id = gm.group_id
        JOIN users u ON e.paid_by = u.user_id
        WHERE gm.user_id = ?
        ORDER BY e.created_at ASC
    """, (user_id,))
    all_expenses = cursor.fetchall()

    recent_activity_items = get_recent_activity_top_3(all_expenses)
    conn.close()

    return render_template(
        'dashboard_view.html',
        username=session.get('username'),
        net_balance=net_balance,
        you_owe_total=you_owe_total,
        you_are_owed_total=you_are_owed_total,
        active_owe_count=active_owe_count,
        active_owed_count=active_owed_count,
        month_tx_count=month_tx_count,
        groups=sorted_group_balances,
        person_debts=person_debt_list,
        recent_activity=recent_activity_items,
        total_groups_count=len(user_groups),
        currency=Config.CURRENCY_SYMBOL
    )