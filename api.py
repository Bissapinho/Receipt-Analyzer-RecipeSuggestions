import requests
import time
import json
import re
import os


API_KEY = "dfzb14GyfmBUGsFkoIawlI375oewd8tA7szqRHk1glUptAF2qsBy6uPWmmrunxKO"

#func to use in the class to handle specific items
def clean_ocr_item(item: str, qty: float):
    """
    Cleans and normalizes an OCR-extracted receipt line.
    """

    if not item:
        return None, None

    #Text normalization
    item = item.strip().lower()
    item = re.sub(r"\s+", " ", item)

    #Remove prices
    item = re.sub(r"\s*\d+(?:[.,]\d+)?\s*€", "", item)

    #Remove promotions / marketing noise
    CLEAN_PATTERN = r"""
        \b(promo|offre|maxi)\b
        |
        \b(format\s+familial|grand\s+format)\b
        |
        \d+\s*x\s*\d+
        |
        \bx\d+\b
        |
        -?\d+%
    """
    item = re.sub(CLEAN_PATTERN, "", item, flags=re.I | re.VERBOSE)

    #Final spacing cleanup
    item = re.sub(r"\s{2,}", " ", item).strip()

    #Handle vrac items
    if "vrac" in item:
        weight_match = re.search(r"([\d,.]+)\s*kg", item)
        if weight_match:
            try:
                qtykg = float(weight_match.group(1).replace(",", "."))
                name = (
                    item.replace(weight_match.group(0), "")
                        .replace("vrac", "")
                        .strip()
                )
                return name, qtykg
            except ValueError:
                return None, None

    #Filter parasitic lines
    bad_words = ("tva", "ht", "kraft", "payer", "merci", "thank")
    if any(word in item for word in bad_words):
        return None, None

    if not item:
        return None, None

    return item, float(qty)


        
class TabscannerClient:
    """
    Silent Tabscanner OCR client.
    Returns a dict {ingredient_name: quantity}.
    """

    def __init__(self, api_key=API_KEY):
        self.api_key = api_key
        self.headers = {"apikey": self.api_key}

    def scan(self, image_path, max_attempts=2, poll_wait=20):
        """
        Returns a dict: {ingredient_name: qty}.
        """

        raw = self._process_receipt(image_path, max_attempts, poll_wait)
        parsed = self._extract_items(raw)

        return parsed  # final output: dict(name → qty)

    

    #Internal funcs for raw and parsed data
    def _process_receipt(self, image_path, max_attempts, poll_wait):

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Upload
        with open(image_path, "rb") as f:
            r = requests.post(
                "https://api.tabscanner.com/api/2/process",
                headers=self.headers,
                files={"image": f},
            )

        js = r.json()
        token = js.get("token") or js.get("id")

        if not token:
            raise RuntimeError(f"Upload failed: {json.dumps(js, indent=2)}")

        result_url = f"https://api.tabscanner.com/api/result/{token}"

        for _ in range(max_attempts):
            time.sleep(poll_wait)
            # Poll
            
            r = requests.get(result_url, headers=self.headers)
            js = r.json()

            status = (js.get("status") or "").lower()

            if status in ("success", "done", "completed"): #if any update in the API
                return js

        raise TimeoutError("Tabscanner took too long to process the receipt.")

    

    
    def _extract_items(self, js):
        """
        Tabscanner JSON → dict {name: qty}
        """

        result = js.get("result") or {}

        # Possible line item locations depending on Tabscanner version
        line_items = (
            result.get("lineItems")
            or result.get("line_items")
            or result.get("data", {}).get("products")
            or []
        )

        items = {}

        for it in line_items:
            # Name extraction (robust)
            name = (
                it.get("descClean")
                or it.get("desc")
                or it.get("description")
                or it.get("item")
                or it.get("name")
            )

            if not name:
                continue


            # Quantity extraction (float)
            qty = it.get("qty") or it.get("quantity") or 1

            try:
                qty = float(qty)
            except:
                qty = 1.0

            name, qty = clean_ocr_item(name, qty)

            if name is None:
                continue

            # Store in dictionary
            items[name] = qty
        
        return items
    


#next remove prices from the item description
