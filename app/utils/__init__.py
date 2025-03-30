from markupsafe import Markup
from flask import current_app

def init_app(app):
    """アプリケーションの初期化時に呼び出される関数"""
    @app.template_filter('cr')
    def cr(text: str) -> Markup:
        """改行コードを<br>に変換する"""
        if not text:
            return Markup("")
        return Markup(text.replace("\n", "<br>")) 