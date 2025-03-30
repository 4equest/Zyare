#!/usr/bin/env python
"""
アプリ起動用スクリプト
"""

from app import create_app, socketio
from dotenv import load_dotenv

load_dotenv()

app = create_app()

if __name__ == "__main__":
    # socketio.run(app, debug=True) など本番環境に合わせて設定してください
    socketio.run(app, debug=True)
