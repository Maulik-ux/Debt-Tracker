# Technique: Stack Abstract Data Type (LIFO)
class Stack:
    """Manual Stack implementation using Last-In, First-Out (LIFO) operations."""
    def __init__(self):
        self._items = []

    def push(self, item):
        """Pushes an element onto the top of the stack."""
        self._items.append(item)

    def pop(self):
        """Pops and returns the top element from the stack."""
        if not self.is_empty():
            return self._items.pop()
        return None

    def peek(self):
        """Returns the top element without removing it."""
        if not self.is_empty():
            return self._items[-1]
        return None

    def is_empty(self):
        """Returns True if the stack is empty."""
        return len(self._items) == 0

    def size(self):
        """Returns the total number of items in the stack."""
        return len(self._items)


def get_recent_activity_top_3(activities):
    """
    Pushes activity records ordered by date onto a Stack, 
    then pops the top 3 items to get the 3 most recent activities.
    """
    stack = Stack()
    
    # Push items chronologically so newest sits on top
    for item in activities:
        stack.push(item)
        
    top_3 = []
    count = 0
    while not stack.is_empty() and count < 3:
        top_3.append(stack.pop())
        count += 1
        
    return top_3