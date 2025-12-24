

This file is to write any specifications that aren't implicit in the code or mentioned anywhere else as to how to run the code.


## Setup

- Create a virtual environment (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install .
```

- Environment variables:
	- Copy [.env.example](.env.example) to `.env` and set `API_KEY` for Tabscanner.

- Ollama requirement:
	- Install Ollama and pull a model (e.g., `llama3.2`). The suggester calls the `ollama` CLI via `subprocess`, so ensure `ollama` is in PATH.

```powershell
winget install Ollama.Ollama
ollama pull llama3.2
```

- Run the app:

```powershell
python Receipt-Analyzer-RecipeSuggestions/main.py
```

