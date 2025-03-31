from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

# ルーティングを読み込む
from . import routes
