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

        # 调用 ollama
        try:
            result = subprocess.run(
                ["ollama", "run", self.model],
                input=prompt,
                text=True,
                capture_output=True,
                encoding='utf-8',  # 强制使用 utf-8 防止编码问题
                check=True  # 如果命令失败则抛出异常
            ).stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Ollama call failed: {e}")
            return []
        except FileNotFoundError:
            print("[ERROR] Ollama not found. Make sure ollama is installed and added to PATH.")
            return []

        # --- 🔍 DEBUG: 打印原始输出，看看 AI 到底回了什么 ---
        print(f"[DEBUG] Raw output from AI:\n{result}\n" + "-" * 30)

        # --- 🧹 清洗数据: 去掉 Markdown 和多余文本 ---
        cleaned_result = self._clean_json(result)

        try:
            parsed = json.loads(cleaned_result)
            return parsed
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON Parse Failed: {e}")
            # 返回错误信息以便在 main.py 中显示
            return [{
                "name": "ModelOutputParseError",
                "ingredients": ["Check console for raw output"],
                "steps": ["The model returned invalid JSON."]
            }]

    def _clean_json(self, text):
        """
        Helper to remove markdown code blocks and find the JSON list.
        """
        # 1. 去掉 markdown 代码块标记
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        # 2. 寻找 JSON 的起止符号 [ ... ]
        start = text.find('[')
        end = text.rfind(']') + 1

        if start != -1 and end != 0:
            return text[start:end]

        return text

    def _build_prompt(self, inventory, n_recipes):
        items = "\n".join([f"- {k}: {v}" for k, v in inventory.items()])

        # 提示词微调：更强烈地要求只返回 JSON
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
    # 简单的测试
    s = RecipeSuggesterOllama()
    print(s.suggest({"egg": 2}))