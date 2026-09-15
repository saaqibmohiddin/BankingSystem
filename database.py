import sqlite3
from pathlib import Path


# Database file location
DATABASE = Path(__file__).parent / "bank.db"


def get_connection():
    """
    Create and return a SQLite database connection.
    """
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    # Enable foreign key support
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database():
    """
    Create the required database tables if they don't already exist.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Accounts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_number INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                pin_hash TEXT NOT NULL,
                balance_paise INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_number INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                amount_paise INTEGER NOT NULL,
                balance_after_paise INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (account_number)
                REFERENCES accounts(account_number)
                ON DELETE CASCADE
            )
        """)

        connection.commit()

    except sqlite3.Error as error:
        connection.rollback()
        print(f"Database initialization error: {error}")

    finally:
        connection.close()