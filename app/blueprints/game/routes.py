from flask import Blueprint, render_template, redirect, url_for, request, abort, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models.room import Room, RoomStatus
from app.models.player import Player
from app.models.note import Note
from app.game_modes.base_mode import BaseGameMode
from app.game_modes import get_game_mode_class
from app.game_modes.normal_mode import NormalGameMode
from app.game_modes.thousand_char_mode import ThousandCharGameMode
from app.game_modes.ai_imposter_mode import AIImposterGameMode
from app.blueprints.game.websockets import (
    broadcast_title_progress,
    broadcast_all_titles_set,
    _broadcast_game_end,
    broadcast_paragraph_progress,
    broadcast_all_paragraphs_submitted
)
from app.utils.background_tasks import run_in_background, run_in_thread_pool

game_bp = Blueprint('game', __name__)

def generate_bot_paragraphs(room_id: int, current_turn: int, game_mode_class: AIImposterGameMode):
    """BOTの文章生成をバックグラウンドで行う"""
    app = current_app._get_current_object()
    
    @run_in_background(app)
    def generate_and_add_paragraph():
        """文章生成とノート追加を一つのタスクとして実行"""
        try:
            room:Room = Room.query.get(room_id)
            if not room:
                return
            players = room.players
            # 現在のターンのノートを取得
            for note in room.notes:
                for player in players:
                    if note.writers[current_turn] == player.user_id and player.user.is_bot:
                        # 前のプレイヤーの投稿を取得
                        previous_content = None
                        if note.contents and len(note.contents) > current_turn-1:
                            previous_content = note.contents[current_turn-1]

                        # BOTの文章を生成
                        new_paragraph = game_mode_class.ai_generate_paragraph(
                            note.title,
                            previous_content["paragraph"] if previous_content else "あなたは最初の書き手なので、前の文章は存在しません。タイトルから物語の始まりを書いてください。"
                        )
                        
                        # 生成した文章をノートに追加
                        note.add_content(player.user_id, new_paragraph)
                        db.session.commit()
                        
                        # WebSocketで新しい段落を通知
                        completed_count = room.written_paragraphs_count()
                        total_players = room.get_players_count(include_bots=False)
                        
                        broadcast_paragraph_progress(room_id, completed_count, total_players)

                        # 全員がパラグラフを投稿したら次のターンへ
                        if completed_count == total_players:
                            broadcast_all_paragraphs_submitted(room_id)
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error in generate_and_add_paragraph: {str(e)}")
            raise
        finally:
            db.session.close()
    
    # バックグラウンドで文章生成とノート追加を実行
    generate_and_add_paragraph()

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
                         total_players=room.get_players_count(include_bots=False))

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
    total_players = room.get_players_count(include_bots=False)

    # 全員がパラグラフを投稿したら次のターンへ
    if completed_count == total_players:
        room.advance_turn()
        db.session.commit()


    # 現在のターンのノートを取得
    current_turn = room.settings.get('current_turn', 0)
    player_order = room.settings.get('player_order', [])
    current_player_id = current_user.id
    
    if room.settings.get('bot_turn', 0) == current_turn:
        if room.settings.get("game_mode", "normal") == "ai_imposter":
            new_settings = room.settings.copy()
            new_settings["bot_turn"] = current_turn + 1
            room.settings = None
            db.session.flush()
            room.settings = new_settings
            db.session.commit()
            generate_bot_paragraphs(room_id, current_turn, game_mode_class)

    
    # 現在のプレイヤーのノートを取得
    current_note = None
    is_bot_turn = True
    previous_content = None
    for note in room.notes:
        if note.writers[current_turn] == str(current_player_id):
            current_note = note
            is_bot_turn = False
            # 前のプレイヤーの投稿を取得
            if current_note.contents and len(current_note.contents) > current_turn-1:
                previous_content = current_note.contents[current_turn-1]
            break

    # ゲーム状態を取得
    game_state = {
        'status': 'playing',
        'current_turn': current_turn,
        'player_order': player_order,
        'total_players': room.get_players_count(include_bots=False),
        'completed_count': room.written_paragraphs_count(),
        'is_bot_turn': is_bot_turn
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