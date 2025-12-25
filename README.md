
# Virtual Fridge Web-Application

## Description
A Python app that scans receipts using OCR (Tabscanner), stores items in a smart fridge, and suggests recipes based on available ingredients using Ollama.

## Features
- Receipt scanning with automatic item extraction
- Per-user fridge inventory management
- AI-powered recipe suggestions (local Ollama)
- History logging of scans and recipes


## Setup

- Create a virtual environment (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
```

- Environment variables:
	- Copy [.env.example](.env.example) to `.env` and set `API_KEY` for Tabscanner.

- Ollama requirement:
	- Install Ollama and pull a model (e.g., `llama3.2`). The suggester calls the `ollama` CLI via `subprocess`, so ensure `ollama` is in PATH.

```powershell
winget install Ollama.Ollama
ollama pull llama3.2
```

## Usage

```powershell
python Receipt-Analyzer-RecipeSuggestions/main.py
```

1. Enter username
2. Choose action: 
	1. scan receipt
	2. get recipes based on current fridge inventory
	3. view current fridge

