import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from api import TabscannerClient
from recipe_suggester_ollama import RecipeSuggesterOllama

app = Flask(__name__)
app.secret_key = "smart_fridge_secret"

UPLOAD_FOLDER = 'uploads'
FRIDGE_DATA_FILE = 'all_fridges.json'
HISTORY_FILE = 'history.json'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class Fridge:
    """Manages inventory with auto-repair capabilities."""

    @staticmethod
    def load_all():
        """Load all data safely."""
        if os.path.exists(FRIDGE_DATA_FILE):
            try:
                with open(FRIDGE_DATA_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}  # Return empty if file is corrupt
        return {}

    @staticmethod
    def save_all(data):
        with open(FRIDGE_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def get_user_inventory(user):
        """
        Retrieves AND automatically fixes corrupted/nested inventory data.
        Fixes the 'Inventory': {...} nesting bug upon loading.
        """
        all_data = Fridge.load_all()
        user_inventory = all_data.get(user, {})

        # --- AUTO-FIX BUG: Check for nested 'Inventory' key ---
        # If the data looks like {'Inventory': {'beef': 1.0, ...}}
        # We flatten it to {'beef': 1.0, ...}
        if 'Inventory' in user_inventory and isinstance(user_inventory['Inventory'], dict):
            print(f"[SYSTEM] Detected nested data for user '{user}'. Auto-fixing...")
            fixed_inventory = user_inventory['Inventory']

            # Update and save immediately
            all_data[user] = fixed_inventory
            Fridge.save_all(all_data)
            return fixed_inventory

        return user_inventory


class HistoryLogger:
    """Robust logging system."""

    @staticmethod
    def load_history():
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    @staticmethod
    def log_action(user, action_type, description):
        history = HistoryLogger.load_history()
        if user not in history:
            history[user] = []

        event = {
            "type": action_type,  # SCAN, COOK, CLEAR
            "desc": description,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        # Newest logs first
        history[user].insert(0, event)

        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=4)


# --- Routes ---

@app.route('/')
def index():
    if 'username' not in session: return redirect(url_for('login'))

    # Use the new auto-fixing method
    user_inventory = Fridge.get_user_inventory(session['username'])

    return render_template('index.html', user=session['username'], inventory=user_inventory)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            session['username'] = username
            # Trigger a load to auto-fix any data immediately upon login
            Fridge.get_user_inventory(username)
            return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/history')
def history():
    """Route to view history logs."""
    if 'username' not in session: return redirect(url_for('login'))

    all_history = HistoryLogger.load_history()
    user_logs = all_history.get(session['username'], [])

    return render_template('history.html', logs=user_logs)


@app.route('/upload', methods=['POST'])
def upload():
    if 'username' not in session: return redirect(url_for('login'))

    file = request.files.get('file')
    if not file or file.filename == '': return redirect(url_for('index'))

    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    client = TabscannerClient()
    new_items = client.scan(path)

    all_data = Fridge.load_all()
    user = session['username']

    # Ensure user dict exists and is not the nested garbage
    if user not in all_data or 'Inventory' in all_data[user]:
        # Reset if it's strictly the wrong format, otherwise get current
        current_inv = Fridge.get_user_inventory(user)
        all_data[user] = current_inv

    # Merge items correctly
    for item, qty in new_items.items():
        all_data[user][item] = all_data[user].get(item, 0) + qty

    Fridge.save_all(all_data)
    HistoryLogger.log_action(user, "SCAN", f"Added {len(new_items)} items.")

    return redirect(url_for('index'))


@app.route('/suggest')
def suggest():
    if 'username' not in session: return redirect(url_for('login'))

    inventory = Fridge.get_user_inventory(session['username'])

    if not inventory:
        return "Your fridge is empty! Please scan a receipt first.", 400

    suggester = RecipeSuggesterOllama()
    recipes = suggester.suggest(inventory)

    if not isinstance(recipes, list):
        recipes = [{
            "name": "System Busy 👩‍🍳",
            "ingredients": ["N/A"],
            "steps": ["The chef is currently offline. Please try again."]
        }]

    return render_template('recipes.html', recipes=recipes)


@app.route('/cook', methods=['POST'])
def cook():
    if 'username' not in session: return redirect(url_for('login'))
    ingredients_needed = request.form.getlist('ingredients')

    all_data = Fridge.load_all()
    user = session['username']

    # Get clean inventory
    inventory = Fridge.get_user_inventory(user)

    deducted_count = 0
    for need in ingredients_needed:
        need_clean = need.lower().strip()
        for stock_item in list(inventory.keys()):
            if need_clean in stock_item.lower() or stock_item.lower() in need_clean:
                inventory[stock_item] = max(0, inventory[stock_item] - 1.0)
                if inventory[stock_item] <= 0:
                    del inventory[stock_item]
                deducted_count += 1
                break

                # Save back the cleaned, updated inventory
    all_data[user] = inventory
    Fridge.save_all(all_data)

    HistoryLogger.log_action(user, "COOK", f"Cooked a meal using {deducted_count} ingredients.")

    return redirect(url_for('index'))


@app.route('/clear', methods=['POST'])
def clear():
    if 'username' not in session: return redirect(url_for('login'))

    all_data = Fridge.load_all()
    all_data[session['username']] = {}
    Fridge.save_all(all_data)

    HistoryLogger.log_action(session['username'], "CLEAR", "Emptied the entire fridge.")

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
