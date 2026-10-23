# Technique: Custom MaxHeap Implementation
class MaxHeap:
    """Max-Heap for priority sorting of net creditors."""
    def __init__(self):
        self.heap = []

    def push(self, amount, person_id):
        self.heap.append((amount, person_id))
        self._sift_up(len(self.heap) - 1)

    def pop(self):
        if not self.heap:
            return None
        if len(self.heap) == 1:
            return self.heap.pop()
        
        root = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._sift_down(0)
        return root

    def _sift_up(self, idx):
        parent = (idx - 1) // 2
        while idx > 0 and self.heap[idx][0] > self.heap[parent][0]:
            self.heap[idx], self.heap[parent] = self.heap[parent], self.heap[idx]
            idx = parent
            parent = (idx - 1) // 2

    def _sift_down(self, idx):
        largest = idx
        left = 2 * idx + 1
        right = 2 * idx + 2
        n = len(self.heap)

        if left < n and self.heap[left][0] > self.heap[largest][0]:
            largest = left
        if right < n and self.heap[right][0] > self.heap[largest][0]:
            largest = right

        if largest != idx:
            self.heap[idx], self.heap[largest] = self.heap[largest], self.heap[idx]
            self._sift_down(largest)

    def __bool__(self):
        return len(self.heap) > 0


# Technique: Custom MinHeap Implementation
class MinHeap:
    """Min-Heap for priority sorting of net debtors (storing negative balances)."""
    def __init__(self):
        self.heap = []

    def push(self, amount, person_id):
        self.heap.append((amount, person_id))
        self._sift_up(len(self.heap) - 1)

    def pop(self):
        if not self.heap:
            return None
        if len(self.heap) == 1:
            return self.heap.pop()
        
        root = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._sift_down(0)
        return root

    def _sift_up(self, idx):
        parent = (idx - 1) // 2
        while idx > 0 and self.heap[idx][0] < self.heap[parent][0]:
            self.heap[idx], self.heap[parent] = self.heap[parent], self.heap[idx]
            idx = parent
            parent = (idx - 1) // 2

    def _sift_down(self, idx):
        smallest = idx
        left = 2 * idx + 1
        right = 2 * idx + 2
        n = len(self.heap)

        if left < n and self.heap[left][0] < self.heap[smallest][0]:
            smallest = left
        if right < n and self.heap[right][0] < self.heap[smallest][0]:
            smallest = right

        if smallest != idx:
            self.heap[idx], self.heap[smallest] = self.heap[smallest], self.heap[idx]
            self._sift_down(smallest)

    def __bool__(self):
        return len(self.heap) > 0


# Technique: Greedy Debt Minimisation Engine
def simplify_group_debts(net_balances_cents):
    """
    Greedy Debt Minimization Algorithm.
    Operates internally using integer cents to prevent floating point inaccuracies.
    """
    creditors = MaxHeap()
    debtors = MinHeap()

    for person_id, balance in net_balances_cents.items():
        if balance > 0:
            creditors.push(balance, person_id)
        elif balance < 0:
            debtors.push(balance, person_id)

    optimized_transactions = []

    while creditors and debtors:
        max_credit, creditor_id = creditors.pop()
        max_debt_neg, debtor_id = debtors.pop()

        max_debt = -max_debt_neg
        settlement_cents = min(max_credit, max_debt)

        optimized_transactions.append({
            'debtor_id': debtor_id,
            'creditor_id': creditor_id,
            'amount': round(settlement_cents / 100.0, 2)
        })

        remaining_credit = max_credit - settlement_cents
        remaining_debt = max_debt - settlement_cents

        if remaining_credit > 0:
            creditors.push(remaining_credit, creditor_id)
        if remaining_debt > 0:
            debtors.push(-remaining_debt, debtor_id)

    return optimized_transactions