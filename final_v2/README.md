
# Virtual Fridge Web Application (final_v2)

MySmartFridge is a Flask web app that turns grocery receipts into per-user fridge inventories and suggests recipes you can cook right now. Upload a receipt image, the app extracts items via Tabscanner OCR, cleans them with a local Ollama model, stores them in your fridge, and lets you cook recipes that auto-deduct ingredients. Everything is stored locally in JSON—no external database required.

## Features

- Receipt OCR (JPG/PNG) via Tabscanner; cleaned and normalized ingredient list
- Per-user fridges created on login; inventories saved to JSON
- Manual inventory management (add, remove, clear)
- Recipe suggestions from a local Ollama model (e.g., llama3.2)
- Cook flow deducts ingredients and logs activity
- Activity and recipe history views
- Local-first storage: `data/` for JSON, `uploads/` for temporary images (auto-deleted)

## Project Structure (final_v2)

- `app.py` – Flask app, routes, session handling, histories
- `api.py` – Tabscanner OCR client and OCR-to-food cleaning
- `fridge.py` – Fridge model with load/save/deduct utilities
- `recipe_suggester_ollama.py` – Ollama prompt + JSON cleaning for recipes
- `templates/` – HTML templates for views
- `data/` – JSON storage (`all_fridges.json`, `history.json`, `recipe_history.json`)
- `uploads/` – Temporary receipt uploads (deleted after processing)
- `tests/global_tests.py` – Ad-hoc functional tests
- `requirements.txt` – Python dependencies (add `Flask` if missing)

## Prerequisites

- Python 3.10+ (tested on Windows)
- Tabscanner API key (set in `.env`)
- Ollama installed and available on PATH
	- Example: `winget install Ollama.Ollama`
	- Start server: `ollama serve`
	- Pull model: `ollama pull llama3.2`
- Internet access for Tabscanner OCR calls

## Setup

1) Create and activate a virtual environment (PowerShell):
```powershell
python -m venv .venv
\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
```

2) Environment variables (.env in `V2/`):
```
API_KEY=your_tabscanner_api_key
```

3) Ensure Ollama is running before recipe suggestions:
```powershell
ollama serve
ollama pull llama3.2
```

## Running the App

From the `V2` directory:
```powershell
python app.py
```
- Default host/port: http://localhost:5001 (Flask debug flag set by `DEBUGGER` in `app.py`).
- Keep Ollama running in another terminal (`ollama serve`).

## Using the App

1) Login: enter any username (creates or loads a per-user fridge).
2) Upload receipt: go to the main page, upload JPG/PNG; OCR runs, items are cleaned, added to your fridge, and the upload is deleted.
3) Manage fridge: add/remove items or clear via the Fridge page.
4) Get recipes: click “Suggest Recipes.” If Ollama is down, the page shows a helpful error.
5) Cook a recipe: selecting Cook deducts ingredients, logs the action, and saves the full recipe to history.
6) View history: Activity history and recipe history pages show past actions and cooked recipes.

## Data and Storage

- `data/all_fridges.json` – per-user inventories
- `data/history.json` – activity logs (scan, cook, clear)
- `data/recipe_history.json` – cooked recipes with ingredients and steps
- `uploads/` – temporary receipt images (removed after processing)

## Testing

- Quick functional script:
```powershell
python tests/global_tests.py
```
- For pytest (if installed):
```powershell
python -m pytest tests/global_tests.py -v
```
Notes: recipe suggester tests require Ollama running; OCR calls need a valid Tabscanner API key.

## Troubleshooting

- Tabscanner API key error: ensure `.env` has `API_KEY` and the file is in `final_v2/`.
- Ollama errors or empty recipes: start `ollama serve` and pull the model; ensure `ollama` is on PATH.
- Empty fridge message: add items manually or upload a receipt first.
- Port already in use: set a different port in `app.py` when calling `app.run`.

