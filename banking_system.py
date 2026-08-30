from database import get_connection, initialize_database


def generate_account_number():
    """Generate a new unique account number."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT MAX(account_number)
        FROM accounts
    """)

    result = cursor.fetchone()[0]
    connection.close()

    if result is None:
        return 100001

    return result + 1


def create_account():
    """Create a new bank account."""
    print("\n--- Create Account ---")

    name = input("Enter your name: ").strip()

    if not name:
        print("\nName cannot be empty.")
        input("\nPress Enter to return to the main menu...")
        return

    pin = input("Create a 4-digit PIN: ").strip()

    if len(pin) != 4 or not pin.isdigit():
        print("\nPIN must contain exactly 4 digits.")
        input("\nPress Enter to return to the main menu...")
        return

    confirm_pin = input("Confirm your PIN: ").strip()

    if pin != confirm_pin:
        print("\nPINs do not match.")
        input("\nPress Enter to return to the main menu...")
        return

    try:
        initial_balance = float(
            input("Enter initial balance: ₹")
        )

        if initial_balance < 0:
            print("\nInitial balance cannot be negative.")
            input("\nPress Enter to return to the main menu...")
            return

    except ValueError:
        print("\nPlease enter a valid amount.")
        input("\nPress Enter to return to the main menu...")
        return

    account_number = generate_account_number()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO accounts
        (account_number, name, pin, balance)
        VALUES (?, ?, ?, ?)
    """, (
        account_number,
        name,
        pin,
        initial_balance
    ))

    if initial_balance > 0:
        cursor.execute("""
            INSERT INTO transactions
            (account_number, transaction_type, amount, balance_after)
            VALUES (?, ?, ?, ?)
        """, (
            account_number,
            "Initial Deposit",
            initial_balance,
            initial_balance
        ))

    connection.commit()
    connection.close()

    print("\nAccount created successfully!")
    print(f"Your Account Number: {account_number}")

    input("\nPress Enter to return to the main menu...")


def get_account(account_number):
    """Find an account using account number."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM accounts
        WHERE account_number = ?
    """, (account_number,))

    account = cursor.fetchone()

    connection.close()

    return account


def deposit():
    """Deposit money into an account."""
    print("\n--- Deposit Money ---")

    account_number = input("Enter account number: ").strip()

    if not account_number.isdigit():
        print("\nInvalid account number.")
        input("\nPress Enter to return to the main menu...")
        return

    account = get_account(int(account_number))

    if account is None:
        print("\nAccount not found.")
        input("\nPress Enter to return to the main menu...")
        return

    try:
        amount = float(
            input("Enter deposit amount: ₹")
        )

    except ValueError:
        print("\nPlease enter a valid amount.")
        input("\nPress Enter to return to the main menu...")
        return

    if amount <= 0:
        print("\nAmount must be greater than zero.")
        input("\nPress Enter to return to the main menu...")
        return

    new_balance = account["balance"] + amount

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE accounts
        SET balance = ?
        WHERE account_number = ?
    """, (
        new_balance,
        int(account_number)
    ))

    cursor.execute("""
        INSERT INTO transactions
        (account_number, transaction_type, amount, balance_after)
        VALUES (?, ?, ?, ?)
    """, (
        int(account_number),
        "Deposit",
        amount,
        new_balance
    ))

    connection.commit()
    connection.close()

    print("\nDeposit successful!")
    print(f"Current Balance: ₹{new_balance:.2f}")

    input("\nPress Enter to return to the main menu...")


def withdraw():
    """Withdraw money from an account."""
    print("\n--- Withdraw Money ---")

    account_number = input("Enter account number: ").strip()

    if not account_number.isdigit():
        print("\nInvalid account number.")
        input("\nPress Enter to return to the main menu...")
        return

    account = get_account(int(account_number))

    if account is None:
        print("\nAccount not found.")
        input("\nPress Enter to return to the main menu...")
        return

    try:
        amount = float(
            input("Enter withdrawal amount: ₹")
        )

    except ValueError:
        print("\nPlease enter a valid amount.")
        input("\nPress Enter to return to the main menu...")
        return

    if amount <= 0:
        print("\nAmount must be greater than zero.")
        input("\nPress Enter to return to the main menu...")
        return

    if amount > account["balance"]:
        print("\nInsufficient balance.")
        input("\nPress Enter to return to the main menu...")
        return

    new_balance = account["balance"] - amount

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE accounts
        SET balance = ?
        WHERE account_number = ?
    """, (
        new_balance,
        int(account_number)
    ))

    cursor.execute("""
        INSERT INTO transactions
        (account_number, transaction_type, amount, balance_after)
        VALUES (?, ?, ?, ?)
    """, (
        int(account_number),
        "Withdrawal",
        amount,
        new_balance
    ))

    connection.commit()
    connection.close()

    print("\nWithdrawal successful!")
    print(f"Current Balance: ₹{new_balance:.2f}")

    input("\nPress Enter to return to the main menu...")


def check_balance():
    """Display account balance."""
    print("\n--- Check Balance ---")

    account_number = input("Enter account number: ").strip()

    if not account_number.isdigit():
        print("\nInvalid account number.")
        input("\nPress Enter to return to the main menu...")
        return

    account = get_account(int(account_number))

    if account is None:
        print("\nAccount not found.")
        input("\nPress Enter to return to the main menu...")
        return

    print(f"\nAccount Holder: {account['name']}")
    print(f"Account Number: {account['account_number']}")
    print(f"Current Balance: ₹{account['balance']:.2f}")

    input("\nPress Enter to return to the main menu...")


def transaction_history():
    """Display transaction history."""
    print("\n--- Transaction History ---")

    account_number = input("Enter account number: ").strip()

    if not account_number.isdigit():
        print("\nInvalid account number.")
        input("\nPress Enter to return to the main menu...")
        return

    account = get_account(int(account_number))

    if account is None:
        print("\nAccount not found.")
        input("\nPress Enter to return to the main menu...")
        return

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            transaction_type,
            amount,
            balance_after,
            created_at
        FROM transactions
        WHERE account_number = ?
        ORDER BY transaction_id DESC
    """, (int(account_number),))

    transactions = cursor.fetchall()

    connection.close()

    if not transactions:
        print("\nNo transactions found.")
        input("\nPress Enter to return to the main menu...")
        return

    print("\nTransaction History")
    print("-" * 80)

    for transaction in transactions:
        print(
            f"{transaction['created_at']} | "
            f"{transaction['transaction_type']} | "
            f"Amount: ₹{transaction['amount']:.2f} | "
            f"Balance: ₹{transaction['balance_after']:.2f}"
        )

    print("-" * 80)

    input("\nPress Enter to return to the main menu...")


def main():
    """Main banking system menu."""
    initialize_database()

    while True:
        print("\n" + "=" * 40)
        print("       BANKING MANAGEMENT SYSTEM")
        print("=" * 40)

        print("1. Create Account")
        print("2. Deposit Money")
        print("3. Withdraw Money")
        print("4. Check Balance")
        print("5. Transaction History")
        print("6. Exit")

        choice = input("\nEnter your choice: ").strip()

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
            break

        else:
            print("\nInvalid choice. Please select 1-6.")


if __name__ == "__main__":
    main()