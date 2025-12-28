import os
import json
from flask import Flask, render_template, request, redirect, url_for, session
from api import TabscannerClient
from recipe_suggester_ollama import RecipeSuggesterOllama

app = Flask(__name__)
app.secret_key = "smart_fridge_secret"  # Security key for session management

UPLOAD_FOLDER = 'uploads'
FRIDGE_DATA_FILE = 'all_fridges.json'

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class Fridge:
    """
    Manages multi-user inventory data persistence using a local JSON file.
    """

    @staticmethod
    def load_all():
        """Load all user data from the JSON database."""
        if os.path.exists(FRIDGE_DATA_FILE):
            with open(FRIDGE_DATA_FILE, 'r') as f:
                return json.load(f)
        return {}

    @staticmethod
    def save_all(data):
        """Save updated data back to the JSON database."""
        with open(FRIDGE_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

@app.route('/')
def index():
    """
    Main Dashboard:
    - Redirects to login if session is empty.
    - Loads current user's inventory for display.
    """
    if 'username' not in session:
        return redirect(url_for('login'))

    all_data = Fridge.load_all()
    user_inventory = all_data.get(session['username'], {})

    return render_template(
        'index.html',
        user=session['username'],
        inventory=user_inventory
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login route:
    - GET: Renders the login page.
    - POST: Establishes a user session.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            session['username'] = username
            return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logs out the user and clears the session."""
    session.clear()
    return redirect(url_for('login'))


@app.route('/upload', methods=['POST'])
def upload():
    """
    Handles receipt upload:
    1. Saves the image.
    2. Triggers Tabscanner OCR + AI cleaning.
    3. Updates the user's inventory in the JSON database.
    """
    if 'username' not in session: return redirect(url_for('login'))

    file = request.files.get('file')
    if not file or file.filename == '': return redirect(url_for('index'))

    # Save image locally
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    # Initialize AI client and scan
    client = TabscannerClient()
    new_items = client.scan(path)

    # Update database
    all_data = Fridge.load_all()
    user = session['username']
    if user not in all_data: all_data[user] = {}

    # Merge new items (accumulate quantities)
    for item, qty in new_items.items():
        all_data[user][item] = all_data[user].get(item, 0) + qty

    Fridge.save_all(all_data)
    return redirect(url_for('index'))


@app.route('/suggest')
def suggest():
    """
    Generates personalized recipe ideas using the local AI model.
    """
    if 'username' not in session: return redirect(url_for('login'))

    all_data = Fridge.load_all()
    inventory = all_data.get(session['username'], {})

    if not inventory:
        return "Your fridge is empty! Please scan a receipt first.", 400

    # Call the recipe suggestion module
    suggester = RecipeSuggesterOllama()
    recipes = suggester.suggest(inventory)

    # Defensive coding: Handle potential AI formatting errors gracefully
    if not isinstance(recipes, list):
        recipes = [{
            "name": "System Busy 👩‍🍳",
            "ingredients": ["N/A"],
            "steps": ["The chef is currently offline. Please try again."]
        }]

    return render_template('recipes.html', recipes=recipes)


@app.route('/cook', methods=['POST'])
def cook():
    """
    Inventory Management:
    - Triggered when a user clicks "Cook this Recipe".
    - Deducts the used ingredients from the user's inventory.
    """
    if 'username' not in session: return redirect(url_for('login'))

    # Retrieve ingredient list from the hidden form inputs
    ingredients_needed = request.form.getlist('ingredients')

    all_data = Fridge.load_all()
    user = session['username']
    inventory = all_data.get(user, {})

    # Logic to match recipe ingredients with inventory items
    for need in ingredients_needed:
        need_clean = need.lower().strip()

        # Fuzzy match: Check if the needed item exists in inventory keys
        for stock_item in list(inventory.keys()):
            if need_clean in stock_item.lower() or stock_item.lower() in need_clean:
                # Deduct 1 unit
                inventory[stock_item] = max(0, inventory[stock_item] - 1.0)

                # Remove item if quantity reaches zero
                if inventory[stock_item] <= 0:
                    del inventory[stock_item]
                break

    Fridge.save_all(all_data)
    return redirect(url_for('index'))


@app.route('/clear', methods=['POST'])
def clear():
    """Resets the current user's inventory to empty."""
    if 'username' not in session: return redirect(url_for('login'))

    all_data = Fridge.load_all()
    all_data[session['username']] = {}
    Fridge.save_all(all_data)

    return redirect(url_for('index'))


if __name__ == '__main__':
    # Run the application on all network interfaces
    app.run(host='0.0.0.0', port=5001, debug=True)
