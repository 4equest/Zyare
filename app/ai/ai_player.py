import os
import random

from litellm import completion

class AIPlayer:
    def generate_paragraph(self, title: str, previous_paragraph: str) -> str:
        prompt = ""
        with open("instance/prompt/base.txt", "r", encoding="utf-8") as f:
            prompt = f.read()
            prompt += "\n"
            

        files = [f for f in os.listdir("instance/prompt") if f.endswith(".txt") and f != "base.txt"]
        if files:
            selected_file = random.choice(files)
            with open(f"instance/prompt/{selected_file}", "r", encoding="utf-8") as f:
                prompt += f.read()
                prompt += "\n"
        
        prompt += f"# タイトル\n{title}\n"
        prompt += f"# 前の文章\n{previous_paragraph}\n"
        response = completion(
            model="gemini/gemini-2.0-flash",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        return response['choices'][0]['message']['content'].strip()
