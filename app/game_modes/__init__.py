from .base_mode import BaseGameMode
from .normal_mode import NormalGameMode
from .thousand_char_mode import ThousandCharGameMode
from .ai_imposter_mode import AIImposterGameMode
from app.models.room import Room

def get_game_mode_class(room: Room) -> type[BaseGameMode]:
    """
    ルームのsettings["game_mode"] を見て、対応するGameModeクラスを返す。
    デフォルトは NormalGameMode とする。
    """
    mode_name = room.settings.get("game_mode", "normal")
    if mode_name == "thousand":
        return ThousandCharGameMode
    elif mode_name == "ai_imposter":
        return AIImposterGameMode
    else:
        return NormalGameMode 