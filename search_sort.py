# Technique: Custom Sorting Algorithm (Selection Sort)
def selection_sort_by_amount(items, reverse=False):
    """
    Sorts a list of dictionaries by the 'amount' key using Selection Sort.
    Does NOT use built-in sorted(), list.sort(), min(), or max().
    """
    arr = list(items)
    n = len(arr)
    
    for i in range(n):
        target_idx = i
        for j in range(i + 1, n):
            val_j = abs(arr[j].get('amount', 0.0))
            val_target = abs(arr[target_idx].get('amount', 0.0))
            
            if reverse:
                if val_j > val_target:
                    target_idx = j
            else:
                if val_j < val_target:
                    target_idx = j
                    
        # Swap elements in-place
        arr[i], arr[target_idx] = arr[target_idx], arr[i]
        
    return arr


# Technique: Custom Linear Search
def linear_search_expenses(expenses, query):
    """
    Performs a linear search over expense records matching description or group name.
    Does NOT use built-in search functions.
    """
    if not query:
        return expenses
        
    query_lower = query.lower()
    results = []
    
    for item in expenses:
        desc = str(item.get('description', '')).lower()
        group = str(item.get('group_name', '')).lower()
        
        if query_lower in desc or query_lower in group:
            results.append(item)
            
    return results