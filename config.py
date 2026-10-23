import os

class Config:
    # Secret key for encrypting browser session cookies
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ib_cs_sl_debt_tracker_secret_key_2026'
    
    # Path to SQLite database file
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'debt_tracker.db')
    
    # Application display constants
    CURRENCY_SYMBOL = '$'
    OVERDUE_DAYS = 15