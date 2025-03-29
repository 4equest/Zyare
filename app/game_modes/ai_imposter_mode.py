from .base_mode import BaseGameMode
import random
from app.ai.ai_player import AIPlayer
from app.utils.helper import random_hiragana

class AIImposterGameMode(BaseGameMode):
    def validate_paragraph(self, paragraph: str) -> bool:
        """AIモードでも通常モード同様のチェック"""
        char_limit = self.room.settings.get("char_limit", 200)
        return len(paragraph) <= char_limit

    def is_game_over(self) -> bool:
        """AIは人間数分のターンで終了"""
        expected_paragraphs = len(self.room.players) * self.room.settings.get("total_rounds", 1)
        current_paragraphs = sum([len(note.contents) for note in self.room.notes])
        return current_paragraphs >= expected_paragraphs

    def calculate_results(self) -> dict:
        """投票結果集計"""
        return {"player_aliases": {player.user_id: random_hiragana() for player in self.room.players}}

    def ai_generate_paragraph(self, note_title: str, previous_paragraph: str) -> str:
        """AIにLitellmで文章作成してもらう"""
        ai_player = AIPlayer()
        return ai_player.generate_paragraph(note_title, previous_paragraph)
