from recipe_suggester_ollama import RecipeSuggesterOllama
from recipe_history import RecipeHistory
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


def show_suggestions(suggestions, history=None):
    """
    Display suggestions using the log function.
    """
    log("\n=== 🍽 Recipe Suggestions ===")

    if not suggestions:
        log("No suggestions available.")
        return None

    for idx, recipe in enumerate(suggestions, 1):
        name = recipe.get('name', 'Unknown Recipe')
        log(f"\n[{idx}] {name}")

        log("Ingredients:")
        for ing in recipe.get("ingredients", []):
            log(f"  - {ing}")

        log("Steps:")
        for step in recipe.get("steps", []):
            log(f"  - {step}")

        # Record view history
        if history:
            history.add(name, status="viewed")

    # User interaction (Input is not logged, but the result is)
    choice = input("\nWhich recipe do you want to accept? (number or Enter to skip): ")

    if choice.strip().isdigit():
        n = int(choice)
        if 1 <= n <= len(suggestions):
            selected = suggestions[n - 1]
            log(f"\n👍 Accepted: {selected.get('name')}")

            if history:
                history.add(selected.get('name'), status="accepted")

            return selected

    log("\nNo recipe selected.")
    return None


# def update_and_show_inventory(inventory, recipe):
#     """
#     Deduct ingredients and log remaining stock.
#     """
#     log("\n=== 📦 Remaining Inventory ===")

#     if recipe:
#         for item in recipe.get('ingredients', []):
#             key = item.lower().strip()
#             if key in inventory:
#                 inventory[key] = max(0, inventory[key] - 1)

#     for item, qty in inventory.items():
#         log(f"- {item}: {qty}")


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

        print(f"\n✅ All data (Suggestions, Inventory, History) exported to '{filename}'")
    except Exception as e:
        print(f"❌ Failed to export: {e}")




def main_recipe_suggestor(user):

    # 1. Setup inventory

    # Here it will take from fridge class for inventory
    # inventory = {
    #     "tomato": 3,
    #     "egg": 4,
    #     "bread": 2,
    #     "onion": 1
    # }

    with open("all_fridges.json", 'r') as f:
        fridge = Fridge.load_fridge(user)
        inventory = fridge.inventory


    # 2. Init modules
    suggester = RecipeSuggesterOllama(model="llama3.2")
    history = RecipeHistory()

    # 3. Get suggestions
    print("Generating recipe suggestions...")  # This is transient, no need to log
    suggestions = suggester.suggest(inventory)

    # 4. Interaction
    accepted_recipe = show_suggestions(suggestions, history)

    # 5. Show Remaining Inventory
    if accepted_recipe:
        fridge.deduct_by_recipe(accepted_recipe)
        fridge.save_fridge()

    # 6. Show History
    log("\n=== 📜 History Records (Current Session) ===")
    for r in history.list():
        # Format: Time | Status | Name
        log(f"{r.timestamp.strftime('%H:%M:%S')} | {r.status.upper()} | {r.name}")

    # 7. Export everything
    save_session_to_file()


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
    choice = input('Do you want to (indicate number): \n [1] Scan a receipt \n [2] Get recipe suggestions \n [3] View your fridge \n')
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
    user = prompt_username()
    while True:
        choice = prompt_menu()
        if choice == "1": scan_and_store_fridge(user)
        elif choice == "2": main_recipe_suggestor(user)
        elif choice == "3": view_fridge(user)
        # elif choice == "history": show_history(user)
        else: break

