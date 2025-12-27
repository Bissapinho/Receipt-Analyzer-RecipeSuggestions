import requests
import time
import json
import re
import os

API_KEY = "dfzb14GyfmBUGsFkoIawlI375oewd8tA7szqRHk1glUptAF2qsBy6uPWmmrunxKO"


def clean_ocr_item(item: str, qty: float):
    if not item:
        return None, None
    item = item.strip().lower()
    item = re.sub(r"\s+", " ", item)
    item = re.sub(r"(€\s*\d+[.,]?\d*|\d+[.,]?\d*\s*(€|eur|/kg))", "", item)

    CLEAN_PATTERN = r"\b(promo|offre|maxi)\b|\b(format\s+familial|grand\s+format)\b|\d+\s*x\s*\d+|\bx\d+\b|-?\d+%"
    item = re.sub(CLEAN_PATTERN, "", item, flags=re.I | re.VERBOSE)
    item = re.sub(r"\s{2,}", " ", item).strip()
    return item, float(qty)


class TabscannerClient:
    def __init__(self, api_key=API_KEY):
        self.api_key = api_key
        self.headers = {"apikey": self.api_key}

    def scan(self, image_path, max_attempts=2, poll_wait=20):
        raw = self._process_receipt(image_path, max_attempts, poll_wait)
        initial_items = self._extract_items(raw)

        cleaned_items = self._ai_refine_list(initial_items)
        return cleaned_items

    def _ai_refine_list(self, items_dict):
        if not items_dict: return {}

        raw_names = ", ".join(items_dict.keys())
        prompt = f"""
        Act as a professional grocery data cleaner.
        Raw list: {raw_names}

        Tasks:
        1. Keep ONLY food items. Remove bags, taxes, and random numbers.
        2. Clean names: Remove codes, '*' symbols, and technical suffixes.
        3. Translate ALL to simple English (e.g., 'viande bovine' -> 'beef').

        Return ONLY a JSON dictionary where keys are English names and values are 1.0.
        Example: {{"beef": 1.0, "mushrooms": 1.0, "coke": 1.0}}
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

            ai_res = response.json()
            cleaned_data = json.loads(ai_res['response'])

            final_dict = {str(name).lower(): 1.0 for name in cleaned_data.keys()}
            return final_dict

        except Exception:
            return {k.replace('*', '').strip(): v for k, v in items_dict.items() if len(k) > 2}

    def _process_receipt(self, image_path, max_attempts, poll_wait):
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        with open(image_path, "rb") as f:
            r = requests.post(
                "https://api.tabscanner.com/api/2/process",
                headers=self.headers,
                files={"image": f}
            )

        js = r.json()
        token = js.get("token") or js.get("id")
        if not token: raise RuntimeError("Upload failed")

        result_url = f"https://api.tabscanner.com/api/result/{token}"
        for _ in range(max_attempts):
            time.sleep(poll_wait)
            r = requests.get(result_url, headers=self.headers)
            js = r.json()
            if js.get("status") in ("success", "done", "completed"):
                return js
        raise TimeoutError("OCR Timeout")

    def _extract_items(self, js):
        result = js.get("result") or {}
        line_items = (
                result.get("lineItems") or
                result.get("line_items") or
                result.get("data", {}).get("products") or
                []
        )
        items = {}
        for it in line_items:
            name = it.get("descClean") or it.get("desc") or it.get("description") or it.get("item") or it.get("name")
            if not name: continue
            qty = it.get("qty") or it.get("quantity") or 1
            name, qty = clean_ocr_item(name, qty)
            if name:
                items[name] = items.get(name, 0) + float(qty)
        return items
