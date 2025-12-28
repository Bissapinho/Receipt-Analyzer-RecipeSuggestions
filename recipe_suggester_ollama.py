import requests
import json
import re


class RecipeSuggesterOllama:
    """
    A robust recipe generator using Ollama (Llama 3.2).
    Includes strong error handling and regex cleaning to prevent parsing errors.
    """

    def __init__(self, model="llama3.2"):
        self.model = model

    def suggest(self, inventory, n_recipes=3):
        """
        Main function to generate recipes.
        Returns a list of dictionaries (or a single error dict if it fails).
        """
        # 1. Prepare ingredients string
        items = ", ".join([k for k in inventory.keys()])

        # 2. Build a very strict prompt
        prompt = f"""
        You are a professional chef API. 
        My ingredients: {items}.

        TASK:
        Create {n_recipes} simple recipes using these ingredients.

        RULES:
        1. Output MUST be valid JSON.
        2. Return a LIST of objects.
        3. ENGLISH ONLY. No intro, no explanation.

        REQUIRED JSON STRUCTURE:
        [
          {{
            "name": "Recipe Name",
            "ingredients": ["item1", "item2"],
            "steps": ["Step 1...", "Step 2..."]
          }}
        ]
        """

        print(f"\n[DEBUG] Sending prompt to Ollama...")

        try:
            # 3. Call Ollama API
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"  # Force JSON mode
                },
                timeout=45
            )

            # 4. Extract raw text response
            ai_res = response.json()
            raw_text = ai_res.get('response', '')

            print(f"[DEBUG] Raw AI Output:\n{raw_text}\n" + "-" * 30)

            # 5. Clean and Parse
            cleaned_json = self._extract_json_array(raw_text)
            parsed_recipes = json.loads(cleaned_json)

            # 6. Validate structure
            if isinstance(parsed_recipes, list) and len(parsed_recipes) > 0:
                return parsed_recipes
            elif isinstance(parsed_recipes, dict):
                # Sometimes AI returns a single object instead of a list
                return [parsed_recipes]

            raise ValueError("Output was valid JSON but not a list or dict.")

        except Exception as e:
            print(f"[ERROR] Recipe Generation Failed: {e}")
            # Return a friendly error recipe so the app doesn't crash
            return [{
                "name": "Chef is Sleeping 😴",
                "ingredients": ["Network Error", "or Bad Format"],
                "steps": [
                    f"Error details: {str(e)}",
                    "Please try clicking 'Find Recipes' again."
                ]
            }]

    def _extract_json_array(self, text):
        """
        Uses Regular Expressions (Regex) to find the JSON list [...]
        hidden inside the text. This fixes the 'Parse Error'.
        """
        # 1. Remove Markdown code blocks (```json ... ```)
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)

        # 2. Find the first '[' and the last ']'
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return match.group(0)  # Return only the list part

        # 3. Fallback: If no list found, try to find a single object '{...}'
        match_obj = re.search(r'\{.*\}', text, re.DOTALL)
        if match_obj:
            return match_obj.group(0)

        # 4. If all fails, return original text (will likely crash in json.loads)
        return text


if __name__ == "__main__":
    # Test block
    s = RecipeSuggesterOllama()
    print(s.suggest({"eggs": 2, "milk": 1}))
