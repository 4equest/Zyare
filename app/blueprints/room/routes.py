import random

from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.room import Room, RoomStatus
from app.models.player import Player
from app.models.note import Note
from app.models.user import User
from app.utils.helper import random_hiragana
from .websockets import _broadcast_player_list, _broadcast_game_start  # <- 追加
from flask_socketio import emit

room_bp = Blueprint('room', __name__)

@room_bp.route('/list')
@login_required
def room_list():
    """参加可能なルーム（WAITING状態）の一覧を表示"""
    rooms = Room.query.filter_by(status=RoomStatus.WAITING).all()
    return render_template('room/list.html', rooms=rooms)

@room_bp.route('/history')
@login_required
def history():
    """過去に参加したルームの一覧を表示"""
    # 現在のユーザーが参加したルームを取得（アーカイブ済みのものも含む）
    rooms = Room.query.join(Player).filter(
        Player.user_id == current_user.id
    ).order_by(Room.created_at.desc()).all()
    return render_template('room/history.html', rooms=rooms)

@room_bp.route('/detail/<int:room_id>')
@login_required
def room_detail(room_id: int):
    """
    ルーム詳細ページ:
    - ルームの基本情報と参加者一覧を表示
    - 参加済みの場合は待機室にリダイレクト
    """
    room = Room.query.get_or_404(room_id)
    
    # 参加済みの場合は待機室にリダイレクト
    if room.status == RoomStatus.WAITING:
        player = Player.query.filter_by(user_id=current_user.id, room_id=room_id).first()
        if player:
            return redirect(url_for('room.waiting', room_id=room_id))

    # ユーザーが参加しているかどうかを確認
    is_participant = Player.query.filter_by(user_id=current_user.id, room_id=room_id).first() is not None

    return render_template('room/detail.html', room=room, players=room.players, is_participant=is_participant)

@room_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_room():
    """新規ルーム作成フォーム"""
    if request.method == 'POST':
        room_name = request.form['room_name']
        room_password = request.form.get('room_password', '')
        chosen_game_mode = request.form.get('game_mode', 'normal')
        total_rounds = int(request.form.get('total_rounds', 2))
        bot_count = int(request.form.get('bot_count', 0)) if chosen_game_mode == 'ai_imposter' else 0

        # AIインポスターモードの場合は、ランダムなひらがなをニックネームとして使用
        if chosen_game_mode == 'ai_imposter':
            nickname = random_hiragana(4)
        else:
            nickname = request.form['nickname']
            
        settings_data = {
            "room_password": room_password,
            "game_mode": chosen_game_mode,
            "bot_count": bot_count,
            "bot_turn": 0,
            "total_rounds": total_rounds
        }
        room = Room(
            name=room_name,
            creator_id=current_user.id,
            settings=settings_data,
            status=RoomStatus.WAITING
        )
        db.session.add(room)
        db.session.commit()

        # 作成者をPlayerとして追加（自動的に準備完了状態）
        player = Player(
            user_id=current_user.id,
            room_id=room.id,
            nickname=nickname,
            is_ready=True  # ルーム作者は自動的に準備完了
        )
        db.session.add(player)
        db.session.commit()

        # AIインポスターモードの場合、BOTを参加させる
        if chosen_game_mode == 'ai_imposter' and bot_count > 0:
            for i in range(bot_count):
                bot = User.query.get(f"bot_{i}")
                if bot:
                    bot_player = Player(
                        user_id=bot.id,
                        room_id=room.id,
                        nickname=random_hiragana(4),  # 4文字のひらがなを生成
                        is_ready=True  # BOTは自動的に準備完了
                    )
                    db.session.add(bot_player)
            db.session.commit()

        flash('ルームを作成しました。')
        return redirect(url_for('room.room_detail', room_id=room.id))

    return render_template('room/create.html')

@room_bp.route('/waiting/<int:room_id>')
@login_required
def waiting(room_id: int):
    """
    待機室ページ:
    - 参加者のみアクセス可能
    - WebSocketでリアルタイム更新
    """
    room = Room.query.get_or_404(room_id)
    player = Player.query.filter_by(user_id=current_user.id, room_id=room_id).first()
    
    if not player:
        flash('このルームに参加していません。')
        return redirect(url_for('room.room_detail', room_id=room_id))

    if room.status != RoomStatus.WAITING:
        flash('待機室はゲーム開始前のみ利用可能です。')
        return redirect(url_for('room.room_detail', room_id=room_id))

    return render_template('room/waiting.html', room=room, players=room.players)

@room_bp.route('/join/<int:room_id>', methods=['POST'])
@login_required
def join_room(room_id: int):
    """
    ルーム参加
    - WAITING状態のルームにのみ参加可能
    - パスワードがある場合は要検証
    - 参加後、待機室へリダイレクト
    """
    room = Room.query.get_or_404(room_id)
    if not room.is_joinable():
        flash('ゲームが開始されているか、このルームは参加不可です。')
        return redirect(url_for('room.room_list'))

    room_pass = request.form.get('room_password', '')
    real_pass = room.settings.get('room_password', None)
    if real_pass and real_pass != room_pass:
        flash('パスワードが違います。')
        return redirect(url_for('room.room_detail', room_id=room_id))

    existing_player = Player.query.filter_by(user_id=current_user.id, room_id=room_id).first()
    if existing_player:
        flash('すでに参加しています。')
        return redirect(url_for('room.waiting', room_id=room_id))

    # AIインポスターモードの場合は、ランダムなひらがなをニックネームとして使用
    if room.settings.get('game_mode') == 'ai_imposter':
        nickname = random_hiragana(4)
    else:
        nickname = request.form['nickname']

    player = Player(user_id=current_user.id, room_id=room_id, nickname=nickname)
    db.session.add(player)
    db.session.commit()

    # 参加したので、WebSocketでプレイヤー一覧更新をブロードキャスト
    _broadcast_player_list(room_id)

    flash('ルームに参加しました。')
    return redirect(url_for('room.waiting', room_id=room_id))

@room_bp.route('/start_game/<int:room_id>', methods=['POST'])
@login_required
def start_game(room_id: int):
    """ルーム作成者のみゲーム開始(状態をPLAYINGに変更)"""
    room = Room.query.get_or_404(room_id)
    if room.creator_id != current_user.id:
        flash('ルーム作成者のみがゲーム開始できます。')
        return redirect(url_for('room.room_detail', room_id=room_id))

    if room.status != RoomStatus.WAITING:
        flash('既にゲームが開始されているか、終了しています。')
        return redirect(url_for('room.room_detail', room_id=room_id))

    # 全員が準備完了かチェック
    all_ready = all(p.is_ready for p in room.players)
    if not all_ready:
        flash('全員が準備完了になるまでゲームを開始できません。')
        return redirect(url_for('room.waiting', room_id=room_id))

    players = room.players  # 参加者リスト
    user_ids = [p.user_id for p in players]
    random.shuffle(user_ids)
    
    new_settings = room.settings.copy()

    new_settings["game_phase"] = "setting_titles"  # ゲームフェーズ: setting_titles -> writing
    new_settings["player_order"] = user_ids  # プレイヤーの順番
    new_settings["current_turn"] = 0  # 現在のターン数
    new_settings["current_phase_turn"] = 0  # 現在のフェーズでのターン数
    
    room.settings = new_settings

    # ノートの作成（BOTを除いたプレイヤーの人数分）
    if not room.notes:  # まだノートが無ければ
        # BOTを除いたプレイヤーを取得
        non_bot_players = [p for p in players if not p.user.is_bot]
        
        # まず、各ノートのwritersを設定
        for i,p in enumerate(non_bot_players):
            new_note = Note(room_id=room.id, contents=[], writers=[])
            user_order = new_settings["player_order"] * (room.settings.get("total_rounds", 2)+1)

            start_index = i

            # 2周分（全体の2倍の長さ）のユーザーIDを連続で選択
            selected_ids = user_order[start_index:start_index + (room.settings.get("total_rounds", 2)) * len(new_settings["player_order"])]
            # 選択した順番で対応するPlayerオブジェクトをnew_note.writersに追加
            for uid in selected_ids:
                new_note.writers.append(uid)
            db.session.add(new_note)
            
        db.session.commit()
        # 次に、タイトルを決めるプレイヤーをランダムに選択して設定
        title_setters = non_bot_players.copy()
        random.shuffle(title_setters)
        for note, title_setter in zip(room.notes, title_setters):
            note.title_setter_player_id = title_setter.user_id

    # その後、room.status = PLAYING
    room.start_game()
    db.session.commit()

    # WebSocketでゲーム開始を通知
    _broadcast_game_start(room_id)

    flash('ゲームを開始しました。')
    return redirect(url_for('game.set_title_page', room_id=room_id))

@room_bp.route('/ready/<int:room_id>', methods=['POST'])
@login_required
def player_ready(room_id: int):
    """
    プレイヤーが「準備完了」ボタンを押したら is_ready の状態を切り替える
    ルーム作者は常に準備完了状態として扱う
    """
    room = Room.query.get_or_404(room_id)
    if room.status != RoomStatus.WAITING:
        flash('すでにゲームが始まっているか、終了しているため準備完了にできません。')
        return redirect(url_for('room.room_detail', room_id=room_id))

    player = Player.query.filter_by(user_id=current_user.id, room_id=room_id).first()
    if not player:
        flash('このルームに参加していません。')
        return redirect(url_for('room.room_detail', room_id=room_id))

    # ルーム作者の場合は常に準備完了状態
    if current_user.id == room.creator_id:
        player.is_ready = True
    else:
        # それ以外のプレイヤーは準備完了状態を切り替え
        player.is_ready = not player.is_ready

    db.session.commit()

    # WebSocketでプレイヤー一覧を更新
    _broadcast_player_list(room_id)
    # ルーム設定も更新
    emit('message', {
        'type': 'room_settings',
        'settings': room.settings,
        'players': [{
            'user_id': p.user_id,
            'nickname': p.nickname,
            'is_ready': p.is_ready
        } for p in room.players]
    }, room=f'room_{room_id}', namespace='/ws/room')

    flash('準備完了状態を更新しました。')
    return redirect(url_for('room.waiting', room_id=room_id))

@room_bp.route('/leave/<int:room_id>', methods=['POST'])
@login_required
def leave_room(room_id: int):
    """
    ルームから退出する処理:
    - WAITING中のみ退出可
    - ゲーム開始後(PLAYING)は不可
    - ルーム作成者が退出する場合、ルームをアーカイブ
    """
    room: Room = Room.query.get_or_404(room_id)
    player: Player|None = Player.query.filter_by(user_id=current_user.id, room_id=room_id).first()
    if not player:
        flash('参加していないため退出できません。')
        return redirect(url_for('room.room_detail', room_id=room_id))

    # ゲーム中か終了後か
    if room.status != RoomStatus.WAITING:
        flash('ゲーム開始後は退出できません。')
        return redirect(url_for('room.room_detail', room_id=room_id))

    # もしルーム作成者が退出 => ルームをアーカイブ
    if current_user.id == room.creator_id:
        # ルームをアーカイブ状態に変更
        room.archive()
        db.session.commit()
        flash('ルーム作成者の退出により、このルームはアーカイブされました。')
        return redirect(url_for('room.room_list'))
    else:
        # 通常退出
        db.session.delete(player)
        db.session.commit()
        # WebSocketでプレイヤー一覧を更新
        _broadcast_player_list(room_id)
        # ルーム設定も更新
        emit('message', {
            'type': 'room_settings',
            'settings': room.settings,
            'players': [{
                'user_id': p.user_id,
                'nickname': p.nickname,
                'is_ready': p.is_ready
            } for p in room.players]
        }, room=f'room_{room_id}', namespace='/ws/room')
        flash('ルームから退出しました。')
        return redirect(url_for('room.room_list'))
