from .base_mode import BaseGameMode

class NormalGameMode(BaseGameMode):
    def validate_paragraph(self, paragraph: str) -> bool:
        """指定された文字数以下ならTrue"""
        char_limit = self.room.settings.get("char_limit", 200)
        return len(paragraph) <= char_limit

    def is_game_over(self) -> bool:
        """参加者数×ターン数で判断"""
        total_rounds = self.room.settings.get("total_rounds", 1)
        expected_paragraphs = len(self.room.players) * total_rounds
        current_paragraphs = sum([len(note.contents) for note in self.room.notes])
        return current_paragraphs >= expected_paragraphs

    def calculate_results(self) -> dict:
        """通常モードには特殊な結果計算なし"""
        return {"notes": [note.contents for note in self.room.notes]}
