from litellm import completion

class AIPlayer:
    def generate_paragraph(self, title: str, previous_paragraph: str) -> str:
        prompt = """# あなたの役割
あなたは物語を書く天才です。奇抜で、先が読めないような短い文章を作成するのが得意です。
あなたは、前の文章を読んで、次の文章を作成します。
ただし、作成する文章は続きが気になるような内容にしてください。
途中で作成を止めてもかまいません。絶対に文章を完結させないでください。
言語は前の文章とタイトルから推察し、推察できない場合は日本語で作成してください。
あなたの出力には、作成する文章が良いの情報を含めないでください。
        """
        
        prompt += f"# タイトル\n{title}\n"
        prompt += f"# 前の文章\n{previous_paragraph}\n"
        response = completion(
            model="gemini-2.0-flash",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        return response['choices'][0]['message']['content'].strip()
