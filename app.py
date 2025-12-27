from flask import Flask, render_template, request, redirect, url_for, session
import os
import re
import json
from datetime import datetime
from fridge import Fridge
from api import TabscannerClient
from recipe_suggester_ollama import RecipeSuggesterOllama

app = Flask(__name__)
app.secret_key = "mysmartfridge_v2_final_key"
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
def index():
    if 'username' not in session:
        return render_template('login.html')
    user = session['username']
    fridge = Fridge.load_fridge(user)
    return render_template('index.html', user=user, inventory=fridge.inventory)


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    if username:
        session['username'] = username
        users_file = 'usernames.json'
        users = json.load(open(users_file)) if os.path.exists(users_file) else []
        if username not in users:
            users.append(username)
            with open(users_file, 'w') as f:
                json.dump(users, f, indent=2)
    return redirect(url_for('index'))


@app.route('/upload', methods=['POST'])
def upload():
    if 'username' not in session: return redirect(url_for('index'))
    file = request.files.get('file')
    if not file or file.filename == '': return redirect(url_for('index'))

    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    results = TabscannerClient().scan(path)
    fridge = Fridge.load_fridge(session['username'])
    fridge.load_from_receipt(results)
    fridge.save_fridge()
    return redirect(url_for('index'))


@app.route('/suggest')
def suggest():
    if 'username' not in session: return redirect(url_for('index'))
    fridge = Fridge.load_fridge(session['username'])
    raw_output = RecipeSuggesterOllama(model="llama3.2").suggest(fridge.inventory)

    try:
        if isinstance(raw_output, str):
            json_match = re.search(r'(\[.*\])', raw_output, re.DOTALL)
            if json_match:
                clean_json = json_match.group(1).replace(",\n]", "\n]").replace(",]", "]")
                suggestions = json.loads(clean_json)
            else:
                suggestions = json.loads(raw_output)
        else:
            suggestions = raw_output
    except Exception:
        suggestions = None

    return render_template('recipes.html', suggestions=suggestions)


@app.route('/accept_recipe', methods=['POST'])
def accept_recipe():
    if 'username' not in session: return redirect(url_for('index'))
    user = session['username']
    recipe_name = request.form.get('recipe_name')
    ingredients_str = request.form.get('ingredients')
    to_remove = [i.strip() for i in ingredients_str.split(',')]

    fridge = Fridge.load_fridge(user)
    for item in to_remove:
        clean_item = item.split(':')[0].strip()
        if clean_item in fridge.inventory:
            fridge.inventory[clean_item] -= 1
            if fridge.inventory[clean_item] <= 0:
                del fridge.inventory[clean_item]
    fridge.save_fridge()

    history_file = f"history_{user}.json"
    history_data = json.load(open(history_file)) if os.path.exists(history_file) else []
    history_data.append({
        "name": recipe_name,
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "ingredients": to_remove
    })
    with open(history_file, 'w') as f:
        json.dump(history_data, f, indent=2)

    return redirect(url_for('index'))


@app.route('/history')
def history_view():
    if 'username' not in session: return redirect(url_for('index'))
    user = session['username']
    history_file = f"history_{user}.json"
    history_data = json.load(open(history_file)) if os.path.exists(history_file) else []
    return render_template('history.html', history=history_data[::-1])


@app.route('/clear', methods=['POST'])
def clear():
    if 'username' not in session: return redirect(url_for('index'))
    fridge = Fridge.load_fridge(session['username'])
    fridge.inventory = {}
    fridge.save_fridge()
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)