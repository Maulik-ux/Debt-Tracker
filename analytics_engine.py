# utils/analytics_engine.py

def calculate_category_breakdown(expenses):
    """
    Calculates total expenditure grouped by category.
    Does NOT use built-in aggregation frameworks or external libraries.
    """
    categories = {}
    for exp in expenses:
        cat = exp.get('category', 'Other')
        amt = float(exp.get('total_amount', 0.0))
        categories[cat] = round(categories.get(cat, 0.0) + amt, 2)
    return categories


def calculate_group_contribution_shares(expenses):
    """
    Calculates total spending grouped by Group Name.
    """
    group_shares = {}
    for exp in expenses:
        grp = exp.get('group_name', 'General')
        amt = float(exp.get('total_amount', 0.0))
        group_shares[grp] = round(group_shares.get(grp, 0.0) + amt, 2)
    return group_shares