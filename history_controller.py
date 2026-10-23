from flask import Blueprint, render_template, request, session, redirect, url_for
from database import get_connection
from utils.search_sort import selection_sort_by_amount, linear_search_expenses
from datetime import datetime
from config import Config

history_bp = Blueprint('history', __name__, url_prefix='/history')

@history_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.landing'))

    user_id = session['user_id']
    group_filter = request.args.get('group', 'All')
    sort_order = request.args.get('sort', 'desc')
    query = request.args.get('q', '').strip()

    conn = get_connection()
    cursor = conn.cursor()

    # Fetch user's active groups for filter pills
    cursor.execute("""
        SELECT g.group_id, g.group_name 
        FROM expense_groups g
        JOIN group_members gm ON g.group_id = gm.group_id
        WHERE gm.user_id = ?
    """, (user_id,))
    user_groups = cursor.fetchall()

    # Query expenses where user paid OR is in split
    cursor.execute("""
        SELECT DISTINCT e.expense_id, e.description, e.total_amount, e.expense_date,
                        e.paid_by, g.group_name, u.username as payer_name
        FROM expenses e
        JOIN expense_groups g ON e.group_id = g.group_id
        JOIN expense_splits es ON e.expense_id = es.expense_id
        JOIN users u ON e.paid_by = u.user_id
        WHERE es.user_id = ? OR e.paid_by = ?
    """, (user_id, user_id))
    raw_expenses = cursor.fetchall()

    processed_list = []
    current_month_str = datetime.now().strftime('%Y-%m')
    net_this_month = 0.0

    for exp in raw_expenses:
        eid = exp['expense_id']
        gid_name = exp['group_name']

        if group_filter != 'All' and gid_name != group_filter:
            continue

        cursor.execute("SELECT amount_owed FROM expense_splits WHERE expense_id = ? AND user_id = ?", (eid, user_id))
        user_split = cursor.fetchone()
        user_share = user_split['amount_owed'] if user_split else 0.0

        if exp['paid_by'] == user_id:
            signed_amount = round(exp['total_amount'] - user_share, 2)
            headline = "- you paid"
        else:
            signed_amount = round(-user_share, 2)
            headline = f"- paid by {exp['payer_name']}"

        # Monthly net tally
        if exp['expense_date'].startswith(current_month_str):
            net_this_month += signed_amount

        processed_list.append({
            'expense_id': eid,
            'description': exp['description'],
            'headline': headline,
            'expense_date': exp['expense_date'],
            'group_name': gid_name,
            'user_share': user_share,
            'total_amount': exp['total_amount'],
            'amount': signed_amount
        })

    # Apply manual linear search
    filtered_list = linear_search_expenses(processed_list, query)

    # Apply manual selection sort
    sorted_list = selection_sort_by_amount(filtered_list, reverse=(sort_order == 'desc'))

    conn.close()

    return render_template(
        'history_view.html',
        expenses=sorted_list,
        groups=user_groups,
        selected_group=group_filter,
        sort_order=sort_order,
        query=query,
        net_this_month=net_this_month,
        currency=Config.CURRENCY_SYMBOL
    )