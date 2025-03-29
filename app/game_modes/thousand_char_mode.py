from .base_mode import BaseGameMode

class ThousandCharGameMode(BaseGameMode):
    def validate_paragraph(self, paragraph: str) -> bool:
        """合計1000字超えないか判定"""
        total_written = sum(len(content['paragraph']) for note in self.room.notes for content in note.contents)
        limit = self.room.settings.get("char_limit", 1000)
        return (total_written + len(paragraph)) <= limit

    def is_game_over(self) -> bool:
        """文字数が制限値ぴったり到達で終了"""
        total_written = sum(len(content['paragraph']) for note in self.room.notes for content in note.contents)
        limit = self.room.settings.get("char_limit", 1000)
        return total_written >= limit

    def calculate_results(self) -> dict:
        """1000字到達結果を返却"""
        return {"total_characters": sum(len(content['paragraph']) for note in self.room.notes for content in note.contents)}
