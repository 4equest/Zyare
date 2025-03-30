from .base_mode import BaseGameMode
from app.models.room import Room

class ThousandCharGameMode(BaseGameMode):
    @staticmethod
    def validate_paragraph(room: Room, paragraph: str) -> bool:
        """合計1000字超えないか判定"""
        total_written = sum(len(content['paragraph']) for note in room.notes for content in note.contents)
        limit = room.settings.get("char_limit", 1000)
        return (total_written + len(paragraph)) <= limit

    @staticmethod
    def is_game_over(room: Room) -> bool:
        """文字数が制限値ぴったり到達で終了"""
        total_written = sum(len(content['paragraph']) for note in room.notes for content in note.contents)
        limit = room.settings.get("char_limit", 1000)
        return total_written >= limit

    @staticmethod
    def calculate_results(room: Room) -> dict:
        """1000字到達結果を返却"""
        return {"total_characters": sum(len(content['paragraph']) for note in room.notes for content in note.contents)}
