import io
import base64
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, session, redirect, url_for
from database import get_connection
from utils.analytics_engine import calculate_category_breakdown, calculate_group_contribution_shares
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

def generate_pie_chart(category_data):
    if not category_data or sum(category_data.values()) == 0:
        return None

    labels = list(category_data.keys())
    values = list(category_data.values())

    fig, ax = plt.subplots(figsize=(5.5, 4.2))
    fig.patch.set_facecolor('#1e293b')
    ax.set_facecolor('#1e293b')

    colors = ['#38bdf8', '#10b981', '#f43f5e', '#fbbf24', '#a855f7']

    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct='%1.1f%%',
        startangle=140,
        colors=colors[:len(labels)],
        textprops=dict(color="#f8fafc", weight="bold")
    )

    for autotext in autotexts:
        autotext.set_color('#0f172a')

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=130, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    return f"data:image/png;base64,{encoded}"


@analytics_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.landing'))

    user_id = session['user_id']
    time_filter = request.args.get('period', 'month')

    conn = get_connection()
    cursor = conn.cursor()

    # Query only user's personal splits across all expenses
    cursor.execute("""
        SELECT e.category, e.expense_date, es.amount_owed as total_amount, g.group_name
        FROM expenses e
        JOIN expense_splits es ON e.expense_id = es.expense_id
        JOIN expense_groups g ON e.group_id = g.group_id
        WHERE es.user_id = ?
    """, (user_id,))
    raw_splits = [dict(row) for row in cursor.fetchall()]
    conn.close()

    now = datetime.now()
    filtered_splits = []

    for sp in raw_splits:
        exp_dt = datetime.strptime(sp['expense_date'], '%Y-%m-%d')
        if time_filter == 'week' and (now - exp_dt).days <= 7:
            filtered_splits.append(sp)
        elif time_filter == 'month' and exp_dt.month == now.month and exp_dt.year == now.year:
            filtered_splits.append(sp)
        elif time_filter == 'year' and exp_dt.year == now.year:
            filtered_splits.append(sp)
        elif time_filter == 'all':
            filtered_splits.append(sp)

    category_data = calculate_category_breakdown(filtered_splits)
    group_shares = calculate_group_contribution_shares(filtered_splits)
    pie_chart_uri = generate_pie_chart(category_data)

    total_spent = sum(category_data.values())

    return render_template(
        'analytics_view.html',
        category_data=category_data,
        group_shares=group_shares,
        pie_chart_uri=pie_chart_uri,
        total_spent=round(total_spent, 2),
        currency=session.get('currency', '$'),
        selected_period=time_filter
    )