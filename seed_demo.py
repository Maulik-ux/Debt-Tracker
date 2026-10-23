import sqlite3
from werkzeug.security import generate_password_hash
from config import Config
from database import init_db

def seed():
    # 1. Initialize the database schema first to build all tables
    init_db()

    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()

    # 2. Safely clear old data
    cursor.execute("DELETE FROM debts;")
    cursor.execute("DELETE FROM expense_splits;")
    cursor.execute("DELETE FROM expenses;")
    cursor.execute("DELETE FROM group_members;")
    cursor.execute("DELETE FROM expense_groups;")
    cursor.execute("DELETE FROM users;")

    # 3. Add Users
    pwd = generate_password_hash("Password123")
    users = [
        ('Maulik', 'maulik@example.com', pwd, 'Admin'),
        ('Rivaan', 'rivaan@example.com', pwd, 'Member'),
        ('John', 'john@example.com', pwd, 'Member'),
        ('Ben', 'ben@example.com', pwd, 'Member'),
        ('Kevin', 'kevin@example.com', pwd, 'Member')
    ]
    cursor.executemany("INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)", users)

    # 4. Add Groups
    cursor.execute("INSERT INTO expense_groups (group_name, created_by) VALUES ('Food Group', 1)")
    cursor.execute("INSERT INTO expense_groups (group_name, created_by) VALUES ('Taxi Group', 1)")
    cursor.execute("INSERT INTO expense_groups (group_name, created_by) VALUES ('Trip Fund', 1)")

    # 5. Add Group Members
    for gid in [1, 2, 3]:
        for uid in [1, 2, 3, 4, 5]:
            cursor.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)", (gid, uid))

    # 6. Add Sample Expenses
    cursor.execute("INSERT INTO expenses (group_id, paid_by, total_amount, description, category, expense_date) VALUES (1, 2, 32.00, 'Taxi', 'Taxi', '2026-10-14')")
    cursor.execute("INSERT INTO expenses (group_id, paid_by, total_amount, description, category, expense_date) VALUES (1, 1, 10.00, 'Snacks', 'Food', '2026-10-14')")
    
    # 7. Add Active Debts
    cursor.execute("INSERT INTO debts (group_id, debtor_id, creditor_id, amount, status) VALUES (1, 1, 2, 10.00, 'ACTIVE')")
    cursor.execute("INSERT INTO debts (group_id, debtor_id, creditor_id, amount, status) VALUES (1, 3, 1, 5.00, 'ACTIVE')")

    conn.commit()
    conn.close()
    print("Database initialized and seeded successfully with demo data!")

if __name__ == '__main__':
    seed()