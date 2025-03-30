from .base_mode import BaseGameMode
from app.models.room import Room

class NormalGameMode(BaseGameMode):
    @staticmethod
    def validate_paragraph(room: Room, paragraph: str) -> bool:
        """指定された文字数以下ならTrue"""
        char_limit = room.settings.get("char_limit", 200)
        return len(paragraph) <= char_limit

    @staticmethod
    def is_game_over(room: Room) -> bool:
        """参加者数×ターン数で判断"""
        total_rounds = room.settings.get("total_rounds", 1)
        expected_paragraphs = len(room.players) * total_rounds
        current_paragraphs = sum([len(note.contents) for note in room.notes])
        return current_paragraphs >= expected_paragraphs

    @staticmethod
    def calculate_results(room: Room) -> dict:
        """通常モードには特殊な結果計算なし"""
        return {"notes": [note.contents for note in room.notes]}
