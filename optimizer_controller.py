from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from database import get_connection
from utils.greedy_engine import simplify_group_debts
from utils.charts import generate_network_graph

optimizer_bp = Blueprint('optimizer', __name__, url_prefix='/optimizer')

@optimizer_bp.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.landing'))

    user_id = session['user_id']
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT g.group_id, g.group_name 
        FROM expense_groups g
        JOIN group_members gm ON g.group_id = gm.group_id
        WHERE gm.user_id = ?
    """, (user_id,))
    user_groups = cursor.fetchall()

    selected_group_id = request.args.get('group_id', type=int) or (user_groups[0]['group_id'] if user_groups else None)

    before_graph = None
    after_graph = None
    before_count = 0
    after_count = 0
    optimization_message = ""

    if selected_group_id:
        cursor.execute("SELECT user_id, username FROM users WHERE user_id IN (SELECT user_id FROM group_members WHERE group_id = ?)", (selected_group_id,))
        user_names = {row['user_id']: row['username'] for row in cursor.fetchall()}

        cursor.execute("SELECT debtor_id, creditor_id, amount FROM debts WHERE group_id = ? AND status = 'ACTIVE'", (selected_group_id,))
        active_debts = [dict(row) for row in cursor.fetchall()]
        before_count = len(active_debts)

        net_balances_cents = {uid: 0 for uid in user_names.keys()}
        for d in active_debts:
            amt_cents = int(round(d['amount'] * 100))
            net_balances_cents[d['creditor_id']] += amt_cents
            net_balances_cents[d['debtor_id']] -= amt_cents

        if before_count > 0:
            before_graph = generate_network_graph(active_debts, user_names)

        if request.method == 'POST':
            optimized_debts = simplify_group_debts(net_balances_cents)
            after_count = len(optimized_debts)

            if before_count == 0 or after_count >= before_count:
                optimization_message = "Transactions are already optimized."
                after_graph = before_graph
            else:
                cursor.execute("UPDATE debts SET status = 'ARCHIVED' WHERE group_id = ? AND status = 'ACTIVE'", (selected_group_id,))
                for opt in optimized_debts:
                    cursor.execute("""
                        INSERT INTO debts (group_id, debtor_id, creditor_id, amount, status)
                        VALUES (?, ?, ?, ?, 'ACTIVE')
                    """, (selected_group_id, opt['debtor_id'], opt['creditor_id'], opt['amount']))
                
                cursor.execute("""
                    INSERT INTO expenses (group_id, paid_by, total_amount, description, category, expense_date)
                    VALUES (?, ?, 0.0, 'Optimization Run', 'Other', CURRENT_DATE)
                """, (selected_group_id, user_id))

                conn.commit()

                pct_reduction = int(round((1 - (after_count / before_count)) * 100))
                optimization_message = f"Reduced from {before_count} to {after_count} transactions - a {pct_reduction}% reduction."

                net_float = {uid: round(cents / 100.0, 2) for uid, cents in net_balances_cents.items()}
                after_graph = generate_network_graph(optimized_debts, user_names, net_balances=net_float, is_after=True)

    conn.close()

    return render_template(
        'optimizer_view.html',
        groups=user_groups,
        selected_group_id=selected_group_id,
        before_graph=before_graph,
        after_graph=after_graph,
        before_count=before_count,
        after_count=after_count,
        message=optimization_message
    )