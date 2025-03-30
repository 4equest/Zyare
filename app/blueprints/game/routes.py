from flask import Blueprint, render_template, redirect, url_for, request, abort, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.room import Room, RoomStatus
from app.models.player import Player
from app.models.note import Note
from app.game_modes.base_mode import BaseGameMode
from app.game_modes import get_game_mode_class
from .websockets import broadcast_new_paragraph, broadcast_result
from app.game_modes.normal_mode import NormalGameMode
from app.game_modes.thousand_char_mode import ThousandCharGameMode
from app.game_modes.ai_imposter_mode import AIImposterGameMode
from app.blueprints.game.websockets import (
    broadcast_title_progress,
    broadcast_all_titles_set,
    _broadcast_game_end
)

game_bp = Blueprint('game', __name__)

@game_bp.route('/set_title/<int:room_id>', methods=['GET'])
@login_required
def set_title_page(room_id: int):
    """タイトル設定ページを表示"""
    room: Room = Room.query.get_or_404(room_id)
    if room.status != RoomStatus.PLAYING:
        flash('このルームは現在ゲーム中ではありません。')
        return redirect(url_for('room.room_detail', room_id=room_id))

    # 参加者かどうか
    if not any(p.user_id == current_user.id for p in room.players):
        flash('ルームに参加していません。')
        return redirect(url_for('room.room_detail', room_id=room_id))

    # 自分のノートを取得
    player_note = Note.query.filter_by(
        room_id=room_id,
        title_setter_player_id=current_user.id
    ).first()
    
    if not player_note:
        flash('ノートが見つかりません。')
        return redirect(url_for('room.room_detail', room_id=room_id))

    return render_template('game/set_title.html',
                         room=room,
                         current_title=player_note.title or '',
                         completed_count=room.written_titles_count(),
                         total_players=len(room.players))

@game_bp.route('/play/<int:room_id>', methods=['GET', 'POST'])
@login_required
def play(room_id: int):
    """ゲームプレイページ"""
    room: Room|None = Room.query.get_or_404(room_id)
    player: Player|None = Player.query.filter_by(user_id=current_user.id, room_id=room_id).first()
    
    if not player:
        flash('このルームに参加していません。')
        return redirect(url_for('room.room_list'))

    if room.status != RoomStatus.PLAYING:
        flash('ゲームが開始されていません。')
        return redirect(url_for('room.room_detail', room_id=room_id))

    # ゲームモードの取得
    game_mode_class = get_game_mode_class(room)
    
    # ゲーム終了チェック
    if game_mode_class.is_game_over(room):
        return redirect(url_for('game.result', room_id=room_id))

    completed_count = room.written_paragraphs_count()
    total_players = len(room.players)

    # 全員がパラグラフを投稿したら次のターンへ
    if completed_count == total_players:
        room.advance_turn()
        db.session.commit()

    # 現在のターンのノートを取得
    current_turn = room.settings.get('current_turn', 0)
    player_order = room.settings.get('player_order', [])
    current_player_id = current_user.id
    
    # 現在のプレイヤーのノートを取得
    current_note = None
    for note in room.notes:
        if note.writers[current_turn] == str(current_player_id):
            current_note = note
            break
    if not current_note:
        flash('ノートが見つかりません。')
        return redirect(url_for('room.room_detail', room_id=room_id))

    # 前のプレイヤーの投稿を取得
    previous_content = None
    if current_note.contents and len(current_note.contents) > current_turn-1:
        previous_content = current_note.contents[current_turn-1]

    # ゲーム状態を取得
    game_state = {
        'status': 'playing',
        'current_turn': current_turn,
        'player_order': player_order,
        'total_players': len(room.players),
        'completed_count': room.written_paragraphs_count()
    }

    return render_template('game/play.html',
                         room=room,
                         game_state=game_state,
                         current_note=current_note,
                         previous_content=previous_content)

@game_bp.route('/end/<int:room_id>', methods=['POST'])
@login_required
def end_game(room_id: int):
    """ゲーム終了処理"""
    room = Room.query.get_or_404(room_id)
    if room.creator_id != current_user.id:
        flash('ルーム作成者のみがゲームを終了できます。')
        return redirect(url_for('game.play', room_id=room_id))

    if room.status != RoomStatus.PLAYING:
        flash('ゲームは既に終了しています。')
        return redirect(url_for('room.room_detail', room_id=room_id))

    # ゲームを終了
    room.end_game()
    db.session.commit()

    # ゲーム終了を通知
    _broadcast_game_end(room_id)

    flash('ゲームを終了しました。')
    return redirect(url_for('room.room_detail', room_id=room_id))

@game_bp.route('/result/<int:room_id>')
@login_required
def result(room_id: int):
    """
    リザルトページ:
      - 参加者以外は閲覧不可
    """
    room = Room.query.get_or_404(room_id)

    if not any(p.user_id == current_user.id for p in room.players):
        flash('参加者のみ結果を閲覧可能です。')
        return redirect(url_for('room.room_detail', room_id=room_id))

    game_mode_class = get_game_mode_class(room)
    results_data = game_mode_class.calculate_results(room)

    # 表示状態を取得または初期化
    visibility_state = room.get_visibility_state()
    if not visibility_state:
        room.initialize_visibility_state()
        visibility_state = room.get_visibility_state()
        db.session.commit()

    return render_template('game/result.html', 
                         room=room, 
                         notes=room.notes, 
                         results=results_data,
                         visibility_state=visibility_state)