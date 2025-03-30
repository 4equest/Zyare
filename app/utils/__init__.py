from markupsafe import Markup
from flask import current_app

@current_app.template_filter('cr')
def cr(text: str) -> Markup:
    """改行コードを<br>に変換する"""
    if not text:
        return Markup("")
    return Markup(text.replace("\n", "<br>")) 