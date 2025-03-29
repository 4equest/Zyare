# config.py
import os

class Config:
    """
    FlaskやDB設定などを集中管理する。
    """
    # DBファイルのパス(環境変数が無い場合は dev.db を作成)
    DB_FILE = os.environ.get("DB_FILE", "dev.db")
    
    SECRET_KEY = os.environ.get("SECRET_KEY", "go_4equest")
    
    # SQLiteローカルファイル
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_FILE}"
