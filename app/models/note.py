# app/models/note.py

from app.extensions import db
from sqlalchemy.dialects.postgresql import JSON
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Mapped

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)

    # 各段落を保持 ([{"writer_id": str, "paragraph": str, "timestamp": str}, ...] )
    contents = db.Column(JSON, default=[])
    title = db.Column(db.String(255), nullable=True)
    # [user_id, user_id, ...]
    writers = db.Column(JSON, default=[])
    title_setter_player_id = db.Column(db.String(50), nullable=True)  # タイトルを決めるプレイヤーのID

    def add_content(self, writer_id: str, paragraph: str) -> None:
        """新しい段落を追加"""
        new_content = self.contents.copy()
        new_content.append({
            "writer_id": writer_id,
            "paragraph": paragraph,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.contents = new_content

    def get_last_content(self) -> dict:
        """最後の段落を取得"""
        return self.contents[-1] if self.contents else None

    def get_last_writer_id(self) -> str:
        """最後に書いたユーザーIDを返す"""
        return self.contents[-1]["writer_id"] if self.contents else None
