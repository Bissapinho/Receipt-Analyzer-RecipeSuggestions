from datetime import datetime
import json
from api import TabscannerClient
from fridge import Fridge
import os

# Global buffer to store all output
SESSION_LOG = []


def log(message=""):
    """
    Prints to console and appends to the session log buffer.
    """
    print(message)
    SESSION_LOG.append(message)


def save_session_to_file(filename="history_log.txt"):
    """
    Writes the entire accumulated session log to the file.
    """
    if not SESSION_LOG:
        return

    try:
        with open(filename, "a", encoding="utf-8") as f:
            # Add a timestamp header for this run
            header = f"\n\n{'=' * 20} Run Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {'=' * 20}"
            f.write(header)

            # Write all logged lines
            for line in SESSION_LOG:
                f.write("\n" + line)

            f.write("\n" + "=" * 60 + "\n")

        print(f"\n All data (Suggestions, Inventory, History) exported to '{filename}'")
    except Exception as e:
        print(f"Failed to export: {e}")


def prompt_username(filename='usernames.json'):
    # Ask for username:
    name = str(input('Enter your username: \n'))

    # Load existing usernames or create empty list
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            usernames = json.load(f)
    else:
        usernames = []
    
    # Add new username if not already exists
    if name not in usernames:
        usernames.append(name)
        with open(filename, 'w') as f:
            json.dump(usernames, f, indent=2)
    
    return name


def prompt_menu():
    choice = input('Do you want to (indicate number): \n [1] Scan a receipt \n [2] View your fridge \n')
    return str(choice)

def scan_and_store_fridge(user):
    # Scan receipt
    file_path = str(input('Please input the path to your receipt:\n'))
    inst = TabscannerClient()
    dic = inst.scan(file_path)

    # Put into fridge
    fridge = Fridge.load_fridge(user)
    fridge.load_from_receipt(dic)
    fridge.save_fridge()

def view_fridge(user, filename='usernames.json'):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            usernames = json.load(f)
    else:
        usernames = []

    if user not in usernames:
        return print(f'{user} does not have a fridge yet')
    
    fridge = Fridge.load_fridge(user)
    print(fridge)


# MAIN APP FUNCTION
def main():
    print("Application started")
    user = prompt_username()
    while True:
        choice = prompt_menu()
        if choice == "1": scan_and_store_fridge(user)
        elif choice == "2": view_fridge(user)
        # elif choice == "history": show_history(user)
        else: break


if __name__ == '__main__':
    main()
