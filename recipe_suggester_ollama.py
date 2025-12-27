import subprocess
import json


class RecipeSuggesterOllama:
    """
    A recipe suggestion module using Ollama local LLM.
    """

    def __init__(self, model="llama3.2"):
        self.model = model

    def suggest(self, inventory, n_recipes=3):
        """
        Generate recipe suggestions based on the inventory.
        """
        prompt = self._build_prompt(inventory, n_recipes)

        print(f"\n[DEBUG] Sending prompt to Ollama ({self.model})...")

        try:
            result = subprocess.run(
                ["ollama", "run", self.model],
                input=prompt,
                text=True,
                capture_output=True,
                encoding='utf-8',  
                check=True  
            ).stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Ollama call failed: {e}")
            return []
        except FileNotFoundError:
            print("[ERROR] Ollama not found. Make sure ollama is installed and added to PATH.")
            return []
            
        print(f"[DEBUG] Raw output from AI:\n{result}\n" + "-" * 30)

        cleaned_result = self._clean_json(result)

        try:
            parsed = json.loads(cleaned_result)
            return parsed
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON Parse Failed: {e}")
            return [{
                "name": "ModelOutputParseError",
                "ingredients": ["Check console for raw output"],
                "steps": ["The model returned invalid JSON."]
            }]

    def _clean_json(self, text):
        """
        Helper to remove markdown code blocks and find the JSON list.
        """
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        start = text.find('[')
        end = text.rfind(']') + 1

        if start != -1 and end != 0:
            return text[start:end]

        return text

    def _build_prompt(self, inventory, n_recipes):
        items = "\n".join([f"- {k}: {v}" for k, v in inventory.items()])

        return f"""
You are a cooking API. 

Available ingredients:
{items}

Suggest {n_recipes} recipes.

Strictly Output JSON ONLY. No intro. No outro. No markdown.
Format:
[
  {{
    "name": "Recipe Name",
    "ingredients": ["item1", "item2"],
    "steps": ["step1", "step2"]
  }}
]
"""


if __name__ == "__main__":
    s = RecipeSuggesterOllama()
    print(s.suggest({"egg": 2}))
