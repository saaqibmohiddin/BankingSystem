import hashlib
import sqlite3
from decimal import Decimal, InvalidOperation
from getpass import getpass

from database import get_connection, initialize_database


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def hash_pin(pin):
    """
    Convert the PIN into a SHA-256 hash.

    Note:
    This is suitable for demonstrating hashing in a student project.
    Real banking systems should use a password hashing algorithm
    such as Argon2id or bcrypt with appropriate security controls.
    """
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()


def format_money(paise):
    """
    Convert paise into a formatted Indian Rupee amount.

    Example:
    500000 paise -> ₹5,000.00
    """
    rupees = Decimal(paise) / Decimal(100)
    return f"₹{rupees:,.2f}"


def money_to_paise(amount):
    """
    Convert a monetary amount into integer paise.

    Example:
    500.50 -> 50050
    """

    try:
        value = Decimal(str(amount))

    except InvalidOperation:
        raise ValueError("Invalid amount.")

    if value <= 0:
        raise ValueError("Amount must be greater than zero.")

    # Only allow maximum 2 decimal places
    if value.as_tuple().exponent < -2:
        raise ValueError("Amount can have maximum 2 decimal places.")

    paise = int(value * 100)

    return paise


def pause():
    """
    Pause before returning to the main menu.
    """
    input("\nPress Enter to continue...")


def get_account_number():
    """
    Ask for and validate an account number.
    """

    account_number = input("Enter account number: ").strip()

    if not account_number.isdigit():
        print("\nInvalid account number.")
        return None

    return int(account_number)


def get_amount():
    """
    Ask the user for a monetary amount.
    """

    amount = input("Enter amount: ₹").strip()

    try:
        return money_to_paise(amount)

    except ValueError as error:
        print(f"\n{error}")
        return None


# ============================================================
# ACCOUNT NUMBER
# ============================================================

def generate_account_number():
    """
    Generate the next account number.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT MAX(account_number)
            FROM accounts
        """)

        result = cursor.fetchone()[0]

        if result is None:
            return 100001

        return result + 1

    except sqlite3.Error as error:
        print(f"Database error: {error}")
        return None

    finally:
        connection.close()


# ============================================================
# GET ACCOUNT
# ============================================================

def get_account(account_number):
    """
    Find an account by account number.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                account_number,
                name,
                pin_hash,
                balance_paise,
                created_at
            FROM accounts
            WHERE account_number = ?
        """, (account_number,))

        return cursor.fetchone()

    except sqlite3.Error as error:
        print(f"Database error: {error}")
        return None

    finally:
        connection.close()


# ============================================================
# VERIFY PIN
# ============================================================

def verify_account():
    """
    Ask for account number and PIN.

    Returns the account if authentication is successful.
    """

    print("\n--- Account Login ---")

    account_number = get_account_number()

    if account_number is None:
        return None

    account = get_account(account_number)

    if account is None:
        print("\nAccount not found.")
        return None

    pin = getpass("Enter 4-digit PIN: ").strip()

    if len(pin) != 4 or not pin.isdigit():
        print("\nPIN must contain exactly 4 digits.")
        return None

    entered_hash = hash_pin(pin)

    if entered_hash != account["pin_hash"]:
        print("\nIncorrect PIN.")
        return None

    print(f"\nWelcome, {account['name']}!")

    return account


# ============================================================
# CREATE ACCOUNT
# ============================================================

def create_account():
    """
    Create a new bank account.
    """

    print("\n" + "=" * 45)
    print(" CREATE BANK ACCOUNT")
    print("=" * 45)

    name = input("Enter your name: ").strip()

    if not name:
        print("\nName cannot be empty.")
        pause()
        return

    # PIN
    pin = getpass("Create a 4-digit PIN: ").strip()

    if len(pin) != 4 or not pin.isdigit():
        print("\nPIN must contain exactly 4 digits.")
        pause()
        return

    confirm_pin = getpass("Confirm your PIN: ").strip()

    if pin != confirm_pin:
        print("\nPINs do not match.")
        pause()
        return

    # Initial balance
    print("\nInitial balance")

    balance_input = input("Enter initial balance: ₹").strip()

    try:
        initial_balance = Decimal(balance_input)

        if initial_balance < 0:
            print("\nInitial balance cannot be negative.")
            pause()
            return

        if initial_balance.as_tuple().exponent < -2:
            print("\nAmount can have maximum 2 decimal places.")
            pause()
            return

        initial_balance_paise = int(initial_balance * 100)

    except InvalidOperation:
        print("\nPlease enter a valid amount.")
        pause()
        return

    account_number = generate_account_number()

    if account_number is None:
        pause()
        return

    pin_hash = hash_pin(pin)

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Create account
        cursor.execute("""
            INSERT INTO accounts (
                account_number,
                name,
                pin_hash,
                balance_paise
            )
            VALUES (?, ?, ?, ?)
        """, (
            account_number,
            name,
            pin_hash,
            initial_balance_paise
        ))

        # Add initial deposit to transaction history
        if initial_balance_paise > 0:

            cursor.execute("""
                INSERT INTO transactions (
                    account_number,
                    transaction_type,
                    amount_paise,
                    balance_after_paise
                )
                VALUES (?, ?, ?, ?)
            """, (
                account_number,
                "Initial Deposit",
                initial_balance_paise,
                initial_balance_paise
            ))

        connection.commit()

        print("\nAccount created successfully!")
        print("-" * 45)
        print(f"Account Holder : {name}")
        print(f"Account Number : {account_number}")
        print(f"Initial Balance: {format_money(initial_balance_paise)}")
        print("-" * 45)

    except sqlite3.IntegrityError:
        connection.rollback()
        print("\nCould not create account. Account number already exists.")

    except sqlite3.Error as error:
        connection.rollback()
        print(f"\nDatabase error: {error}")

    finally:
        connection.close()

    pause()


# ============================================================
# DEPOSIT
# ============================================================

def deposit():
    """
    Deposit money into an account.
    """

    print("\n" + "=" * 45)
    print(" DEPOSIT MONEY")
    print("=" * 45)

    account = verify_account()

    if account is None:
        pause()
        return

    amount_paise = get_amount()

    if amount_paise is None:
        pause()
        return

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Get latest balance directly from database
        cursor.execute("""
            SELECT balance_paise
            FROM accounts
            WHERE account_number = ?
        """, (account["account_number"],))

        result = cursor.fetchone()

        if result is None:
            print("\nAccount not found.")
            connection.rollback()
            pause()
            return

        current_balance = result["balance_paise"]

        new_balance = current_balance + amount_paise

        # Update balance
        cursor.execute("""
            UPDATE accounts
            SET balance_paise = ?
            WHERE account_number = ?
        """, (
            new_balance,
            account["account_number"]
        ))

        # Add transaction
        cursor.execute("""
            INSERT INTO transactions (
                account_number,
                transaction_type,
                amount_paise,
                balance_after_paise
            )
            VALUES (?, ?, ?, ?)
        """, (
            account["account_number"],
            "Deposit",
            amount_paise,
            new_balance
        ))

        connection.commit()

        print("\nDeposit successful!")
        print(f"Deposited : {format_money(amount_paise)}")
        print(f"New Balance: {format_money(new_balance)}")

    except sqlite3.Error as error:
        connection.rollback()
        print(f"\nTransaction failed: {error}")

    finally:
        connection.close()

    pause()


# ============================================================
# WITHDRAW
# ============================================================

def withdraw():
    """
    Withdraw money from an account.
    """

    print("\n" + "=" * 45)
    print(" WITHDRAW MONEY")
    print("=" * 45)

    account = verify_account()

    if account is None:
        pause()
        return

    amount_paise = get_amount()

    if amount_paise is None:
        pause()
        return

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Get latest balance
        cursor.execute("""
            SELECT balance_paise
            FROM accounts
            WHERE account_number = ?
        """, (account["account_number"],))

        result = cursor.fetchone()

        if result is None:
            print("\nAccount not found.")
            connection.rollback()
            pause()
            return

        current_balance = result["balance_paise"]

        # Check balance
        if amount_paise > current_balance:
            print("\nInsufficient balance.")
            print(f"Available Balance: {format_money(current_balance)}")
            connection.rollback()
            pause()
            return

        new_balance = current_balance - amount_paise

        # Update balance
        cursor.execute("""
            UPDATE accounts
            SET balance_paise = ?
            WHERE account_number = ?
        """, (
            new_balance,
            account["account_number"]
        ))

        # Add transaction
        cursor.execute("""
            INSERT INTO transactions (
                account_number,
                transaction_type,
                amount_paise,
                balance_after_paise
            )
            VALUES (?, ?, ?, ?)
        """, (
            account["account_number"],
            "Withdrawal",
            amount_paise,
            new_balance
        ))

        connection.commit()

        print("\nWithdrawal successful!")
        print(f"Withdrawn  : {format_money(amount_paise)}")
        print(f"New Balance: {format_money(new_balance)}")

    except sqlite3.Error as error:
        connection.rollback()
        print(f"\nTransaction failed: {error}")

    finally:
        connection.close()

    pause()


# ============================================================
# CHECK BALANCE
# ============================================================

def check_balance():
    """
    Display account balance.
    """

    print("\n" + "=" * 45)
    print(" CHECK BALANCE")
    print("=" * 45)

    account = verify_account()

    if account is None:
        pause()
        return

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                name,
                account_number,
                balance_paise,
                created_at
            FROM accounts
            WHERE account_number = ?
        """, (account["account_number"],))

        result = cursor.fetchone()

        if result is None:
            print("\nAccount not found.")
            return

        print("\nAccount Details")
        print("-" * 45)
        print(f"Account Holder : {result['name']}")
        print(f"Account Number : {result['account_number']}")
        print(f"Current Balance: {format_money(result['balance_paise'])}")
        print(f"Created At     : {result['created_at']}")
        print("-" * 45)

    except sqlite3.Error as error:
        print(f"\nDatabase error: {error}")

    finally:
        connection.close()

    pause()


# ============================================================
# TRANSACTION HISTORY
# ============================================================

def transaction_history():
    """
    Display transaction history for an account.
    """

    print("\n" + "=" * 45)
    print(" TRANSACTION HISTORY")
    print("=" * 45)

    account = verify_account()

    if account is None:
        pause()
        return

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                transaction_id,
                transaction_type,
                amount_paise,
                balance_after_paise,
                created_at
            FROM transactions
            WHERE account_number = ?
            ORDER BY transaction_id DESC
        """, (account["account_number"],))

        transactions = cursor.fetchall()

        if not transactions:
            print("\nNo transactions found.")
            pause()
            return

        print()
        print("-" * 90)
        print(
            f"{'ID':<5}"
            f"{'TYPE':<20}"
            f"{'AMOUNT':<18}"
            f"{'BALANCE':<18}"
            f"{'DATE':<20}"
        )
        print("-" * 90)

        for transaction in transactions:

            print(
                f"{transaction['transaction_id']:<5}"
                f"{transaction['transaction_type']:<20}"
                f"{format_money(transaction['amount_paise']):<18}"
                f"{format_money(transaction['balance_after_paise']):<18}"
                f"{transaction['created_at']:<20}"
            )

        print("-" * 90)

    except sqlite3.Error as error:
        print(f"\nDatabase error: {error}")

    finally:
        connection.close()

    pause()


# ============================================================
# MAIN MENU
# ============================================================

def main():
    """
    Main banking system menu.
    """

    initialize_database()

    while True:

        print("\n")
        print("=" * 50)
        print("       BANKING MANAGEMENT SYSTEM")
        print("=" * 50)

        print("1. Create Account")
        print("2. Deposit Money")
        print("3. Withdraw Money")
        print("4. Check Balance")
        print("5. Transaction History")
        print("6. Exit")

        print("=" * 50)

        choice = input("Enter your choice: ").strip()

        if choice == "1":

            create_account()

        elif choice == "2":

            deposit()

        elif choice == "3":

            withdraw()

        elif choice == "4":

            check_balance()

        elif choice == "5":

            transaction_history()

        elif choice == "6":

            print("\nThank you for using Banking Management System.")
            print("Goodbye!")
            break

        else:

            print("\nInvalid choice. Please select 1-6.")
            pause()


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":
    main()