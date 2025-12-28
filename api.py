import requests
import time
import json
import re
import os
from dotenv import load_dotenv

 

# Tabscanner API Key
load_dotenv()
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY not found in .env file")


def clean_ocr_item(item: str, qty: float):
    """
    Clean and normalize raw OCR text from receipt line items.

    Responsibilities:
    - Lowercase and normalize whitespace
    - Remove prices, units, promotions, and marketing keywords
    - Return a clean item name and numeric quantity

    Parameters:
        item (str): Raw OCR-extracted item description
        qty (float): Detected quantity (default is usually 1)

    Returns:
        tuple(str | None, float | None):
            - Cleaned item name (or None if invalid)
            - Quantity as float
    """
    if not item:
        return None, None

    item = item.lower().strip()
    item = re.sub(r"\s+", " ", item)

    #Extract weight FIRST (before cleaning)
    weight_kg = None

    # 0,156kg | 0.156 kg | 156 g
    weight_match = re.search(r"([\d.,]+)\s*(kg|g)", item)
    if weight_match:
        val, unit = weight_match.groups()
        try:
            val = float(val.replace(",", "."))
            weight_kg = val if unit == "kg" else val / 1000
        except ValueError:
            pass

    # Remove prices
    item = re.sub(r"\d+[.,]?\d*\s*(€|eur|€/kg)", "", item)
    item = re.sub(r"(€\s*\d+[.,]?\d*)", "", item)

    #Remove packaging / units
    item = re.sub(r"\b\d+\s*(kg|g|cl|ml|l)\b", "", item)

    #Remove promos & noise
    item = re.sub(
        r"\b(promo|offre|maxi|format|familial|bio)\b"
        r"|\d+\s*x\s*\d+"
        r"|\bx\d+\b"
        r"|-?\d+%",
        "",
        item,
        flags=re.I,
    )

    # Final cleanup
    item = re.sub(r"[^a-z\s]", "", item)
    item = re.sub(r"\s{2,}", " ", item).strip()

    if not item or len(item) < 3:
        return None, None

    #Qty logic
    if weight_kg:
        return item, weight_kg

    try:
        return item, float(qty) if qty else 1.0
    except (TypeError, ValueError):
        return item, 1.0


class TabscannerClient:
    """
    Client wrapper for:
    - Tabscanner OCR API
    - Local LLM-based grocery item refinement (Ollama)

    Pipeline:
    Image -> OCR -> Raw Items -> LLM Refinement -> Clean Food List
    """

    def __init__(self, api_key=API_KEY):
        """
        Initialize client with API key and headers.
        """
        self.api_key = api_key
        self.headers = {"apikey": self.api_key}

    def scan(self, image_path, max_attempts=2, poll_wait=20):
        """
        Full receipt scanning pipeline.

        Steps:
        1. Upload image to Tabscanner
        2. Poll OCR result
        3. Extract raw items
        4. Use LLM to refine and translate items

        Returns:
            dict: {clean_food_name: quantity}
        """
        raw_result = self._process_receipt(image_path, max_attempts, poll_wait)
        initial_items = self._extract_items(raw_result)

        # LLM-based post-processing (LLM Refinement)
        refined_items = self._ai_refine_list(initial_items)
        return refined_items

    def _ai_refine_list(self, items_dict):
        """
        Refine and normalize grocery items using a local LLM (Ollama).

        This method performs semantic post-processing that is difficult
        to achieve reliably with rule-based logic alone.

        Responsibilities:
        - Remove non-food items (bags, deposits, taxes, receipts)
        - Translate item names from French to English
        - Normalize product naming to generic food categories
        - Preserve original quantities exactly

        Parameters:
            items_dict (dict):
                Dictionary of cleaned OCR items in the form:
                {item_name: quantity}

        Returns:
            dict:
                Refined dictionary with English food item names
                and unchanged quantities.
        """
        if not items_dict:
            return {}


        # Prompt engineered for deterministic JSON output
        prompt = f"""
            You are a grocery receipt post-processor.

            You are given a Python dictionary where:
            - keys = OCR-extracted item names (mostly French)
            - values = quantities (floats or ints)

            INPUT DICTIONARY:
            {items_dict}

            YOUR TASK:
            1. Modify ONLY the KEYS.
            2. NEVER change the VALUES.
            3. Translate food items to simple, generic English (e.g. "porc" → "pork").
            4. Normalize product names (remove brands, packaging, units like 33cl, 500g).
            5. Remove NON-FOOD items (bags, deposits, taxes, receipts).
            6. Clean symbols (*, codes, barcodes).

            STRICT RULES:
            - If an item is removed, remove its key-value pair entirely.
            - For kept items, copy the ORIGINAL quantity EXACTLY.
            - DO NOT infer, rescale, round, merge, or invent quantities.
            - Output MUST be valid JSON.
            - Output MUST be a dictionary.
            - Output language: English only.
            - DO NOT merge multiple items into one key.

            EXAMPLE:
            Input:
            {{"porc demi sel 500g": 2, "sac kraft": 1}}

            Output:
            {{"pork": 2}}

            Return ONLY the JSON dictionary.
            """

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )

            # Ollama returns JSON inside the "response" field
            ai_response = response.json()
            cleaned_data = json.loads(ai_response["response"])

            # Quantity is normalized to 1.0 for now
            return {
                str(name).lower().strip(): float(qty)
                for name, qty in cleaned_data.items()
            }


        except Exception:
            # Fallback strategy:
            # If LLM fails, return lightly cleaned OCR results
            return {
                k.replace("*", "").strip(): v
                for k, v in items_dict.items()
                if len(k) > 2
            }

    def _process_receipt(self, image_path, max_attempts, poll_wait):
        """
        Upload receipt image to Tabscanner and poll until OCR is completed.

        Raises:
            FileNotFoundError: If image path does not exist
            TimeoutError: If OCR does not finish in time
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Step 1: Upload receipt image
        with open(image_path, "rb") as f:
            response = requests.post(
                "https://api.tabscanner.com/api/2/process",
                headers=self.headers,
                files={"image": f}
            )

        js = response.json()
        token = js.get("token") or js.get("id")
        if not token:
            raise RuntimeError("Receipt upload failed")

        # Step 2: Poll OCR result endpoint
        result_url = f"https://api.tabscanner.com/api/result/{token}"
        for _ in range(max_attempts):
            time.sleep(poll_wait)
            r = requests.get(result_url, headers=self.headers)
            js = r.json()
            if js.get("status") in ("success", "done", "completed"):
                return js

        raise TimeoutError("OCR processing timed out")

    def _extract_items(self, js):
        """
        Parse Tabscanner OCR JSON into a basic item-quantity dictionary.

        This method is defensive and supports multiple possible
        Tabscanner response schemas.
        """
        result = js.get("result") or {}

        # Handle multiple possible field names from Tabscanner
        line_items = (
            result.get("lineItems")
            or result.get("line_items")
            or result.get("data", {}).get("products")
            or []
        )

        items = {}
        for it in line_items:
            # Try multiple possible keys for item description
            name = (
                it.get("descClean")
                or it.get("desc")
                or it.get("description")
                or it.get("item")
                or it.get("name")
            )
            if not name:
                continue

            qty = it.get("qty") or it.get("quantity") or 1
            name, qty = clean_ocr_item(name, qty)

            if name:
                items[name] = items.get(name, 0) + float(qty)

        return items