import requests
import time
import json
import re
import os

# Your Tabscanner API Key
API_KEY = "dfzb14GyfmBUGsFkoIawlI375oewd8tA7szqRHk1glUptAF2qsBy6uPWmmrunxKO"

def clean_ocr_item(item: str, qty: float):
    """Simple rule-based cleaning of OCR text."""
    if not item:
        return None, None

    item = item.lower().strip()
    item = re.sub(r"\s+", " ", item)

    # Remove prices and symbols
    item = re.sub(r"\d+[.,]?\d*\s*(€|eur|/kg)", "", item)
    item = re.sub(r"[^a-z\s]", "", item)
    item = re.sub(r"\s{2,}", " ", item).strip()

    if not item or len(item) < 3:
        return None, None

    return item, float(qty)

class TabscannerClient:
    def __init__(self, api_key=API_KEY):
        self.api_key = api_key
        self.headers = {"apikey": self.api_key}

    def scan(self, image_path, max_attempts=2, poll_wait=20):
        raw_result = self._process_receipt(image_path, max_attempts, poll_wait)
        initial_items = self._extract_items(raw_result)
        return self._ai_refine_list(initial_items)

    def _ai_refine_list(self, items_dict):
        """Standard LLM refinement that normalizes qty to 1.0."""
        if not items_dict:
            return {}

        prompt = f"""
            Act as a grocery data cleaner. 
            Translate these items to English and remove non-food items: {list(items_dict.keys())}
            Return ONLY a JSON dictionary where values are 1.0.
            Example: {{"milk": 1.0, "bread": 1.0}}
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
            ai_response = response.json()
            cleaned_data = json.loads(ai_response["response"])
            # Standardizing to 1.0 as per original version
            return {str(name).lower().strip(): 1.0 for name in cleaned_data.keys()}
        except Exception:
            return {k: 1.0 for k in items_dict.keys() if len(k) > 2}

    def _process_receipt(self, image_path, max_attempts, poll_wait):
        with open(image_path, "rb") as f:
            response = requests.post("https://api.tabscanner.com/api/2/process",
                                     headers=self.headers, files={"image": f})
        token = response.json().get("token")
        result_url = f"https://api.tabscanner.com/api/result/{token}"
        for _ in range(max_attempts):
            time.sleep(poll_wait)
            r = requests.get(result_url, headers=self.headers)
            js = r.json()
            if js.get("status") in ("success", "done"):
                return js
        raise TimeoutError("OCR Timeout")

    def _extract_items(self, js):
        result = js.get("result") or {}
        line_items = result.get("lineItems") or []
        items = {}
        for it in line_items:
            name = it.get("descClean") or it.get("desc")
            if name:
                name, qty = clean_ocr_item(name, 1)
                if name: items[name] = 1.0
        return items