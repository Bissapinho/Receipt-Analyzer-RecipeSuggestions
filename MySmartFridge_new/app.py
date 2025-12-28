import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from fridge import Fridge
from api import TabscannerClient
from recipe_suggester_ollama import RecipeSuggesterOllama

app = Flask(__name__)
app.secret_key = "smart_fridge_v2_stable_final"

# Configuration for file storage
UPLOAD_FOLDER = 'uploads'
DATA_DIR = 'data'
HISTORY_FILE = 'history.json'
FRIDGE_FILE = os.path.join(DATA_DIR, 'all_fridges.json')

# Initialize directory structure
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)


class HistoryLogger:
    """Utility to log user actions for the history view."""

    @staticmethod
    def log_action(user, action_type, description):
        history = {}
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r') as f:
                    history = json.load(f)
            except:
                history = {}
        if user not in history:
            history[user] = []

        history[user].insert(0, {
            "type": action_type,
            "desc": description,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=4)

@app.route('/')
def index():
    """Main dashboard to view current fridge contents."""
    if 'username' not in session:
        return redirect(url_for('login'))

    # Load inventory using teammate's class
    user_fridge = Fridge.load_fridge(session['username'], filename=FRIDGE_FILE)
    return render_template('index.html', user=session['username'], inventory=user_fridge.inventory)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles simple user login session."""
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            session['username'] = username
            return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/fridge')
def manage_fridge():
    """Dedicated page for manual inventory adjustments."""
    if 'username' not in session:
        return redirect(url_for('login'))

    user_fridge = Fridge.load_fridge(session['username'], filename=FRIDGE_FILE)
    return render_template('fridge.html', inventory=user_fridge.inventory)


@app.route('/upload', methods=['POST'])
def upload():
    """Processes receipt uploads using OCR and AI refinement."""
    if 'username' not in session: return redirect(url_for('login'))

    file = request.files.get('file')
    if not file: return redirect(url_for('index'))

    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    # Trigger scanning pipeline
    client = TabscannerClient()
    new_items = client.scan(path)

    # Load and save data via Fridge class
    user_fridge = Fridge.load_fridge(session['username'], filename=FRIDGE_FILE)
    user_fridge.load_from_receipt(new_items)
    user_fridge.save_fridge(filename=FRIDGE_FILE)

    HistoryLogger.log_action(session['username'], "SCAN", "Updated fridge via OCR scan.")
    return redirect(url_for('index'))


@app.route('/suggest')
def suggest():
    """Generates recipe suggestions based on current fridge items."""
    if 'username' not in session: return redirect(url_for('login'))

    user_fridge = Fridge.load_fridge(session['username'], filename=FRIDGE_FILE)
    if not user_fridge.inventory:
        return "Fridge is empty!", 400

    suggester = RecipeSuggesterOllama()
    recipes = suggester.suggest(user_fridge.inventory)
    return render_template('recipes.html', recipes=recipes)


@app.route('/cook', methods=['POST'])
def cook():
    """Removes used ingredients after cooking a selected recipe."""
    if 'username' not in session: return redirect(url_for('login'))

    recipe_data = {
        "name": request.form.get('recipe_name'),
        "ingredients": request.form.getlist('ingredients')
    }

    user_fridge = Fridge.load_fridge(session['username'], filename=FRIDGE_FILE)
    if user_fridge.has_items(recipe_data):
        user_fridge.deduct_by_recipe(recipe_data)
        user_fridge.save_fridge(filename=FRIDGE_FILE)
        HistoryLogger.log_action(session['username'], "COOK", f"Cooked: {recipe_data['name']}")

    return redirect(url_for('index'))


@app.route('/manual_update', methods=['POST'])
def manual_update():
    """Adds or removes items manually through fridge.html."""
    if 'username' not in session: return redirect(url_for('login'))

    item = request.form.get('item')
    qty = float(request.form.get('qty', 1))
    action = request.form.get('action')

    user_fridge = Fridge.load_fridge(session['username'], filename=FRIDGE_FILE)
    if action == 'add':
        user_fridge.add_item(item, qty)
    else:
        user_fridge.remove_item(item, qty)

    user_fridge.save_fridge(filename=FRIDGE_FILE)
    return redirect(url_for('manage_fridge'))


@app.route('/clear', methods=['POST'])
def clear():
    """Clears the entire inventory for the current user."""
    if 'username' not in session:
        return redirect(url_for('login'))

    user_fridge = Fridge.load_fridge(session['username'], filename=FRIDGE_FILE)
    user_fridge.inventory = {}  # Manually reset
    user_fridge.save_fridge(filename=FRIDGE_FILE)

    HistoryLogger.log_action(session['username'], "CLEAR", "Emptied the fridge.")
    return redirect(url_for('manage_fridge'))


@app.route('/history')
def history():
    """View log of all past activities."""
    if 'username' not in session: return redirect(url_for('login'))

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            all_history = json.load(f)
    else:
        all_history = {}

    user_logs = all_history.get(session['username'], [])
    return render_template('history.html', logs=user_logs)


if __name__ == '__main__':
    if not os.path.exists(FRIDGE_FILE) or os.path.getsize(FRIDGE_FILE) < 2:
        with open(FRIDGE_FILE, 'w') as f:
            json.dump({}, f)
    app.run(host='0.0.0.0', port=5001, debug=True)