
# Version 0: Virtual Fridge Web-Application 

## Description
A simple Python app that uses API OCR (Tabscanner) to scan supermarket grocery receipts and stores items in a virtual fridge.

## Features
- Login with username
- Receipt scanning with automatic item extraction, input needed is the image filepath on computer
- Per-user fridge inventory management
- Logging in main script and saves sessions to history_log.txt
- Simple database management with 2 json files: all_fridges.json and usernames.json, that store information from previous sessions

## Setup

- Create a virtual environment (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
```

- Environment variables:
	- set `API_KEY` for Tabscanner.
	- Development API_KEY: `dfzb14GyfmBUGsFkoIawlI375oewd8tA7szqRHk1glUptAF2qsBy6uPWmmrunxKO`
	- only 200 API calls available per day
	- if calls run out go to: [text](https://tabscanner.com/), create account and insert new key in api.py as `API_KEY` 

## Usage

```powershell
python Receipt-Analyzer-RecipeSuggestions/main.py
```

1. Enter username
2. Choose action: 
	1. scan receipt
	2. get recipes based on current fridge inventory
	3. view current fridge

