from flask import Flask, render_template, request, session, redirect, url_for
from fridge import Fridge
from recipe_suggester_ollama import RecipeSuggesterOllama
from api import TabscannerClient
import os

app = Flask(__name__)
app.secret_key = "your-secret-key"  # For sessions

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('menu'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username
        return redirect(url_for('menu'))
    return render_template('login.html')

@app.route('/menu')
def menu():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('menu.html', username=session['username'])

@app.route('/fridge')
def view_fridge():
    if 'username' not in session:
        return redirect(url_for('login'))
    fridge = Fridge.load_fridge(session['username'])
    return render_template('fridge.html', inventory=fridge.inventory)

@app.route('/recipes')
def get_recipes():
    if 'username' not in session:
        return redirect(url_for('login'))
    fridge = Fridge.load_fridge(session['username'])
    suggester = RecipeSuggesterOllama(model="llama3.2")
    recipes = suggester.suggest(fridge.inventory)
    return render_template('recipes.html', recipes=recipes)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
