from .base_mode import BaseGameMode
import random
from app.ai.ai_player import AIPlayer
from app.utils.helper import random_hiragana
from app.models.room import Room

class AIImposterGameMode(BaseGameMode):
    @staticmethod
    def validate_paragraph(room: Room, paragraph: str) -> bool:
        """AIモードでも通常モード同様のチェック"""
        char_limit = room.settings.get("char_limit", 200)
        return len(paragraph) <= char_limit

    @staticmethod
    def is_game_over(room: Room) -> bool:
        """AIは人間数分のターンで終了"""
        expected_paragraphs = room.get_players_count(include_bots=True) * room.settings.get("total_rounds", 2)
        current_paragraphs = sum([len(note.contents) for note in room.notes])
        return current_paragraphs >= expected_paragraphs

    @staticmethod
    def calculate_results(room: Room) -> dict:
        """投票結果集計"""
        return {"player_aliases": {player.user_id: random_hiragana() for player in room.players}}

    @staticmethod
    def ai_generate_paragraph(note_title: str, previous_paragraph: str) -> str:
        """AIにLitellmで文章作成してもらう"""
        ai_player = AIPlayer()
        return ai_player.generate_paragraph(note_title, previous_paragraph)
