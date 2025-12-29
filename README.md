
# Virtual Fridge Web-Application

## Description

MySmartFridge is a lightweight Flask web app that turns grocery receipts into a per-user, searchable fridge inventory and suggests recipes you can cook right now. Upload a receipt image to extract items via the Tabscanner OCR API; the app normalizes and saves those items into your personal fridge. You can browse and edit your inventory, generate AI-powered recipe ideas using a local Ollama model, and “cook” a recipe to automatically deduct the used ingredients. All actions are logged to a per-user history. Data is stored locally in JSON files (no database required).

## Features

- Receipt OCR: Upload a receipt image (JPG/PNG); items are extracted automatically via Tabscanner.
- Per-user fridges: Simple login creates a personal inventory isolated per user.
- Inventory management: Add/remove/clear items; items are stored locally in JSON.
- Recipe suggestions: Uses a local Ollama model (e.g., llama3.2) to suggest recipes from what you have.
- Cook flow: Deducts recipe ingredients from your fridge in one click.
- Activity history: Logs key actions (scan, cook, clear) for each user.
- Local-first storage: JSON files in the `data/` folder; uploads kept in `uploads/`.
- Resilient parsing: Defensive JSON cleaning to handle imperfect model output.


## Setup

- Create a virtual environment (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
```

- Environment variables:
	- Go to `.env` and set `API_KEY` for Tabscanner.

- Ollama requirement:
	- Install Ollama and pull a model (e.g., `llama3.2`). The suggester calls the `ollama` CLI via `subprocess`, so ensure `ollama` is in PATH.

```powershell
winget install Ollama.Ollama
ollama serve
ollama pull llama3.2
```

## Usage

```powershell
python Receipt-Analyzer-RecipeSuggestions/app.py
```
Go to browser and paste http://localhost:5000 into address bar.
If this doesn't work copy the first link in terminal: eg. Running on 'http://127.0.0.1:5001'.

Make sure ollama is running and in path.

1. Enter username
2. Choose action: 
	1. Scan receipt by uploading an image stored on computer.
	2. Get recipe suggestions based on current fridge inventory.
	3. view current fridge

Press ```ctrl + C ``` to stop running app in corresponding terminal.
Press ```ctrl + C ``` to stop running ollama in corresponding terminal.

