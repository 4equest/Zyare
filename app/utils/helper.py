import random

def random_password():
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))

def random_hiragana(length: int = 4) -> str:
    """
    指定された長さのランダムなひらがな文字列を生成する

    Args:
        length (int): 生成するひらがなの長さ

    Returns:
        str: 生成されたひらがな文字列
    """
    # ひらがなの Unicode 範囲: 3041-3096 (例示)
    hiragana_start = 0x3041
    hiragana_end = 0x3096
    return ''.join(chr(random.randint(hiragana_start, hiragana_end)) for _ in range(length))



def get_next_writer_id(note, room) -> str:
    """
    全ノート同時進行型:
    - noteのインデックス + room.settings["current_turn"] を用いて
      room.settings["player_order"] の誰が執筆するかを決定。
    """
    settings = room.settings
    if "player_order" not in settings or "current_turn" not in settings:
        return None  # 未設定の場合

    player_order = settings["player_order"]  # list of user_id
    current_turn = settings["current_turn"]   # int
    note_idx = get_note_index(note, room)
    if note_idx < 0:
        return None

    p = len(player_order)
    writer = player_order[(note_idx + current_turn) % p]
    return writer

def get_next_writer_for_note(note, room) -> str:
    """
    ノートの最後に書いたユーザーを取得し、room.settings["player_order"] の次の人を返す。
    - note.get_last_writer_id() が現在の筆者
    - そこが player_order の何番目かを探し、その +1 のインデックスを返す
    """
    if "player_order" not in room.settings:
        return None  # ランダム順序未設定時など

    last_writer = note.get_last_writer_id()  # 最後(または初期)のライター
    if not last_writer:
        return None

    player_order = room.settings["player_order"]
    if last_writer not in player_order:
        return None

    idx = player_order.index(last_writer)
    next_idx = (idx + 1) % len(player_order)
    return player_order[next_idx]

def get_note_index(note, room) -> int:
    """
    ルーム内ノートを特定の順序でソートし、noteが何番目か(0-based)を返す。
    ここではID昇順を採用。
    """
    sorted_notes = sorted(room.notes, key=lambda n: n.id)
    for idx, n in enumerate(sorted_notes):
        if n.id == note.id:
            return idx
    return -1  # 見つからない場合(理論上ありえない)