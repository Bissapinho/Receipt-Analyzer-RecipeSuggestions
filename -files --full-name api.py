import requests
import time
import json
import os


API_KEY = "dfzb14GyfmBUGsFkoIawlI375oewd8tA7szqRHk1glUptAF2qsBy6uPWmmrunxKO"


class TabscannerClient:
    """
    Silent Tabscanner OCR client.
    Returns a dict {ingredient_name: quantity}.
    """

    def __init__(self, api_key=API_KEY):
        self.api_key = api_key
        self.headers = {"apikey": self.api_key}

    def scan(self, image_path, max_wait=90, poll_interval=2):
        """
        Returns a dict: {ingredient_name: qty}.
        """

        raw = self._process_receipt(image_path, max_wait, poll_interval)
        parsed = self._extract_items(raw)

        return parsed  # final output: dict(name → qty)

    

    #Internal funcs for raw and parsed data
    def _process_receipt(self, image_path, max_wait, poll_interval):

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

        # Poll
        result_url = f"https://api.tabscanner.com/api/result/{token}"

        for _ in range(max_wait // poll_interval):
            time.sleep(poll_interval)
            r = requests.get(result_url, headers=self.headers)
            js = r.json()

            status = (js.get("status") or "").lower()

            if status in ("success", "done", "completed"):
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
                it.get("desc")
                or it.get("description")
                or it.get("item")
                or it.get("name")
            )

            if not name:
                continue

            name = name.strip().lower()

            # Quantity extraction (float)
            qty = it.get("qty") or it.get("quantity") or 1

            try:
                qty = float(qty)
            except:
                qty = 1.0

            # Store in dictionary
            items[name] = qty

        return items
