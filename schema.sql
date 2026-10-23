-- Enable foreign key support
PRAGMA foreign_keys = ON;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'Member',
    currency TEXT DEFAULT '$',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Expense Groups table
CREATE TABLE IF NOT EXISTS expense_groups (
    group_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT NOT NULL,
    created_by INTEGER NOT NULL,
    status TEXT DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Group Members mapping table
CREATE TABLE IF NOT EXISTS group_members (
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (group_id, user_id),
    FOREIGN KEY (group_id) REFERENCES expense_groups(group_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Expenses table
CREATE TABLE IF NOT EXISTS expenses (
    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    paid_by INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    description TEXT NOT NULL,
    category TEXT DEFAULT 'Other',
    split_type TEXT DEFAULT 'Equally',
    expense_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES expense_groups(group_id) ON DELETE CASCADE,
    FOREIGN KEY (paid_by) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Expense Splits table
CREATE TABLE IF NOT EXISTS expense_splits (
    split_id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    amount_owed REAL NOT NULL,
    FOREIGN KEY (expense_id) REFERENCES expenses(expense_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Debts table (Tracks active, settled, and archived optimized debts)
CREATE TABLE IF NOT EXISTS debts (
    debt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    expense_id INTEGER,
    debtor_id INTEGER NOT NULL,
    creditor_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    status TEXT DEFAULT 'ACTIVE', -- ACTIVE, SETTLED, ARCHIVED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    settled_at TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES expense_groups(group_id) ON DELETE CASCADE,
    FOREIGN KEY (expense_id) REFERENCES expenses(expense_id) ON DELETE SET NULL,
    FOREIGN KEY (debtor_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (creditor_id) REFERENCES users(user_id) ON DELETE CASCADE
);