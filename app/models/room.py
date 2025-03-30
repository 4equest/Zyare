from app.extensions import db
from sqlalchemy.dialects.postgresql import JSON
from typing import List
from enum import Enum
from sqlalchemy.orm import Mapped

class RoomStatus(Enum):
    WAITING = "waiting"    # 参加可能
    PLAYING = "playing"    # ゲーム中
    ARCHIVED = "archived"  # アーカイブ済み

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    creator_id = db.Column(db.String(50), db.ForeignKey('user.id'), nullable=False)
    
    # 進行状態をEnumで管理
    status = db.Column(
        db.Enum(RoomStatus, native_enum=False),
        default=RoomStatus.WAITING,
        nullable=False
    )
    
    settings = db.Column(JSON, default={})
    from app.models.player import Player
    from app.models.note import Note
    players:Mapped[List[Player]] = db.relationship("Player", backref="room", lazy=True)
    notes:Mapped[List[Note]] = db.relationship("Note", backref="room", lazy=True)

    def archive(self) -> None:
        """ルームのアーカイブ"""
        self.status = RoomStatus.ARCHIVED

    def is_joinable(self) -> bool:
        """
        ゲーム開始前( WAITING )なら参加可能とする。
        """
        return self.status == RoomStatus.WAITING
    
    def start_game(self):
        """ゲーム開始時の初期設定"""
        self.status = RoomStatus.PLAYING


    def finish_game(self) -> None:
        """ルームをゲーム終了状態にする。"""
        self.status = RoomStatus.ARCHIVED
    def is_title_setting_phase(self) -> bool:
        """タイトル設定フェーズかどうか"""
        return self.status == RoomStatus.PLAYING and self.settings.get("game_phase") == "setting_titles"

    def is_writing_phase(self) -> bool:
        """文章作成フェーズかどうか"""
        return self.status == RoomStatus.PLAYING and self.settings.get("game_phase") == "writing"

    def get_current_player_id(self) -> int:
        """現在のターンのプレイヤーIDを取得"""
        player_order = self.settings.get("player_order", [])
        current_turn = self.settings.get("current_turn", 0)
        return player_order[current_turn % len(player_order)]

    def advance_turn(self):
        """ターンを進める"""
        current_turn = self.settings.get("current_turn", 0)
        new_settings = self.settings.copy()
        new_settings["current_turn"] = current_turn + 1
        self.settings = new_settings

                
    def written_titles_count(self) -> int:
        """タイトル設定済みのノート数を取得"""
        count = 0
        for note in self.notes:
            if note.title:
                count += 1
        return count

    def written_paragraphs_count(self) -> int:
        """現在のターンで投稿を完了したプレイヤーの数を取得"""
        current_turn = self.settings.get("current_turn", 0)
        count = 0
        
        for note in self.notes:
            # 現在のターンで投稿されているかチェック
            if note.contents and len(note.contents) > current_turn:
                count += 1
                
        return count

    def get_visibility_state(self) -> dict:
        """表示状態を取得"""
        return self.settings.get('visibility_state', None)

    def initialize_visibility_state(self) -> None:
        """表示状態を初期化"""
        new_settings = self.settings.copy()
        visibility_state = {}
        for note in self.notes:
            visibility_state[str(note.id)] = {
                str(i): i == 0 for i in range(len(note.contents))
            }
        new_settings['visibility_state'] = visibility_state
        self.settings = new_settings
        db.session.commit()


    def is_all_paragraphs_visible(self) -> bool:
        """全てのパラグラフが表示されているかどうか"""
        visibility_state = self.get_visibility_state()
        return all(
            all(visible for visible in paragraphs.values())
            for paragraphs in visibility_state.values()
        )

    def get_players_count(self, include_bots: bool = False) -> int:
        """プレイヤー数を取得"""
        count = 0
        for player in self.players:
            if include_bots or not player.user.is_bot:
                count += 1
        return count
