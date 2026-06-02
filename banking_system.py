accounts = {}

while True:
    print("\n--- Banking System ---")
    print("1. Create Account")
    print("2. Deposit")
    print("3. Withdraw")
    print("4. Check Balance")
    print("5. Exit")

    choice = input("Enter choice: ")

    if choice == "1":
        acc_no = input("Enter Account Number: ")
        name = input("Enter Name: ")
        balance = float(input("Enter Initial Balance: "))

        accounts[acc_no] = {
            "name": name,
            "balance": balance
        }

        print("Account Created Successfully!")

    elif choice == "2":
        acc_no = input("Enter Account Number: ")
        amount = float(input("Enter Deposit Amount: "))

        if acc_no in accounts:
            accounts[acc_no]["balance"] += amount
            print("Amount Deposited!")
        else:
            print("Account Not Found!")

    elif choice == "3":
        acc_no = input("Enter Account Number: ")
        amount = float(input("Enter Withdrawal Amount: "))

        if acc_no in accounts:
            if accounts[acc_no]["balance"] >= amount:
                accounts[acc_no]["balance"] -= amount
                print("Withdrawal Successful!")
            else:
                print("Insufficient Balance!")
        else:
            print("Account Not Found!")

    elif choice == "4":
        acc_no = input("Enter Account Number: ")

        if acc_no in accounts:
            print("Balance:", accounts[acc_no]["balance"])
        else:
            print("Account Not Found!")

    elif choice == "5":
        print("Thank You!")
        break

    else:
        print("Invalid Choice!")