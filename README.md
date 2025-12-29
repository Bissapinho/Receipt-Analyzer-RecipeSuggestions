# MySmartFridge - Receipt Analyzer & Recipe Suggester

## Description
A Python command-line application that scans grocery receipts using OCR (Tabscanner API), manages a virtual fridge inventory for multiple users, and generates AI-powered recipe suggestions based on available ingredients using Ollama.

## Features
- **Receipt Scanning**: Upload receipt images for automatic OCR processing and item extraction via Tabscanner API
- **Multi-User Support**: Per-user fridge inventory with persistent JSON storage
- **Inventory Management**: Add items from receipts, view current fridge contents, and automatic ingredient deduction when cooking
- **AI Recipe Suggestions**: Generate recipe recommendations based on available ingredients using local Ollama LLM (llama3.2 model)
- **Recipe History**: Track viewed and accepted recipes with timestamps
- **Session Logging**: Export all actions (scans, suggestions, inventory changes) to `history_log.txt`
- **Smart Cleaning**: Advanced OCR text normalization to handle prices, promotions, and weight measurements

## Prerequisites

### Required Software
- **Python 3.7+** (tested with Python 3.13.5)
- **Ollama** for local LLM recipe generation
- **Tabscanner API Key** for OCR functionality

### Ollama Installation
Install Ollama and pull the llama3.2 model (Windows PowerShell):

```powershell
winget install Ollama.Ollama
ollama pull llama3.2
```

Ensure `ollama` is added to your system PATH so it can be called via command line.

## Setup

### 1. Create Virtual Environment
In the project directory (Windows PowerShell):

```powershell
python -m venv .popvenv
.\.popvenv\Scripts\Activate.ps1
python -m pip install -U pip
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

Required packages include:
- `requests` - HTTP client for Tabscanner API
- `tabulate` - Pretty-print inventory tables
- `python-dotenv` - Environment variable management
- `ollama` - Ollama Python client

### 3. Configure Environment Variables
Create a `.env` file in the project root with your Tabscanner API key:

```env
API_KEY=your_tabscanner_api_key_here
```

Alternatively, the API key is hardcoded in `api.py` (line 7) for testing purposes.

## Usage

### Starting the Application
Run from the project directory:

```powershell
python main.py
```

### Application Workflow

1. **Enter Username**: The app will prompt for a username (creates new user if doesn't exist)

2. **Main Menu Options**:
   - `[1] Scan a receipt` - Upload receipt image for OCR processing
   - `[2] Get recipe suggestions` - Generate AI recipes based on current fridge inventory
   - `[3] View your fridge` - Display current inventory table
   - `[4] Exit Application` - Quit and save session log

3. **Scanning Receipts**:
   - Provide the full file path to your receipt image
   - Tabscanner API processes the image and extracts items
   - Items are automatically added to your fridge inventory
   - Cleaned and normalized for better recognition

4. **Getting Recipe Suggestions**:
   - AI generates 3 recipe suggestions using available ingredients
   - Each recipe includes name, ingredients list, and cooking steps
   - Select a recipe by number to accept it
   - Accepted recipes deduct ingredients from your fridge
   - All actions logged to session history

5. **Session Export**:
   - All activities saved to `history_log.txt` with timestamps
   - Includes recipe views, acceptances, and inventory changes

## Project Structure

```
Receipt-Analyzer-RecipeSuggestions/
├── main.py                      # Main application entry point
├── fridge.py                    # Fridge class for inventory management
├── api.py                       # Tabscanner API client
├── recipe_suggester_ollama.py   # Ollama integration for recipe generation
├── recipe_history.py            # Recipe tracking utilities
├── all_fridges.json             # Persistent storage for all user inventories
├── usernames.json               # List of registered users
├── history_log.txt              # Session activity logs
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (API keys)
├── .popvenv/                    # Python virtual environment
└── __pycache__/                 # Python bytecode cache
```

## Data Storage

- **all_fridges.json**: Stores per-user inventory in format `{username: {inventory: {item: quantity}}}`
- **usernames.json**: Simple list of registered usernames
- **history_log.txt**: Append-only log file with timestamped sessions

## Technical Details

### OCR Processing
- Uses Tabscanner API for receipt scanning
- Automatic text cleaning: removes prices, promotions, duplicates
- Handles bulk/weight items (e.g., "500g flour" → "flour": 0.5)
- Normalizes quantities and item names

### Recipe Generation
- Calls local Ollama LLM via subprocess
- Model: llama3.2
- Generates structured JSON output with recipes
- Robust JSON parsing with fallback error handling
- Handles incomplete or malformed LLM responses

### Inventory Management
- Case-insensitive item matching
- Automatic quantity aggregation
- Supports fractional quantities
- Deducts ingredients when recipes are cooked

## Troubleshooting

**Ollama not found error**:
- Ensure Ollama is installed and added to PATH
- Verify with: `ollama --version`

**Tabscanner API errors**:
- Check your API key in `.env` or `api.py`
- Verify internet connection for API requests

**JSON parsing errors**:
- Enhanced cleaning handles most malformed outputs
- Check console for debug output from Ollama

**Empty fridge after scanning**:
- Verify receipt image quality
- Check `history_log.txt` for extracted items

## Development Notes

- Virtual environment name: `.popvenv`
- Python version: 3.13.5
- Tested on Windows with PowerShell
- Tabscanner API endpoint hardcoded in `api.py`

## License

Educational project for Introduction to Python course.

