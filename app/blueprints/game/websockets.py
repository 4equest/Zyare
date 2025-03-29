# app/blueprints/game/websockets.py
from datetime import datetime
from flask_socketio import emit, join_room
from flask import request
from flask_login import current_user
from app.extensions import socketio, db
from app.models.room import Room, RoomStatus
from app.models.note import Note
from app.models.player import Player

def broadcast_new_paragraph(room_id: int, writer_id: str, paragraph: str) -> None:
    """
    サーバー内から呼び出し:
    - 新規パラグラフ追加後、同じWSルーム("room_{room_id}")へ通知
    """
    payload = {
        'writer_id': writer_id,
        'paragraph': paragraph
    }
    socketio.emit('new_paragraph', payload, room=f'room_{room_id}')

def broadcast_result(room_id: int, result_data: dict) -> None:
    """
    ゲーム終了時や結果集計時にリアルタイムでresultページへ送信
    """
    socketio.emit('show_result_update', result_data, room=f'room_{room_id}')
    
def broadcast_title_progress(room_id: int, completed_count: int, total_players: int):
    """タイトル設定の進捗状況をブロードキャスト"""
    emit('title_progress', {
        'completed_count': completed_count,
        'total_players': total_players
    }, room=f'room_{room_id}', namespace='/ws/game')

def broadcast_all_titles_set(room_id: int):
    """全員がタイトルを設定したことを通知"""
    emit('all_titles_set', room=f'room_{room_id}', namespace='/ws/game')
    
def _broadcast_game_state(room_id: int, game_state: dict):
    """ゲームの状態を通知"""
    room = Room.query.get(room_id)
    if not room:
        return

    emit('game_state', game_state, room=f'room_{room_id}', namespace='/ws/game')

def _broadcast_player_turn(room_id: int, current_player_id: int):
    """プレイヤーのターンを通知"""
    room = Room.query.get(room_id)
    if not room:
        return

    emit('player_turn', {
        'current_player_id': current_player_id
    }, room=f'room_{room_id}', namespace='/ws/game')

def _broadcast_game_end(room_id: int):
    """ゲーム終了を通知"""
    room = Room.query.get(room_id)
    if not room:
        return

    emit('game_end', {
        'room_id': room_id,
        'redirect_url': f'/room/detail/{room_id}'
    }, room=f'room_{room_id}', namespace='/ws/game')

def broadcast_paragraph_progress(room_id: int, completed_count: int, total_players: int):
    """パラグラフ投稿の進捗状況をブロードキャスト"""
    emit('paragraph_progress', {
        'completed_count': completed_count,
        'total_players': total_players
    }, room=f'room_{room_id}', namespace='/ws/game')

def broadcast_all_paragraphs_submitted(room_id: int):
    """全員がパラグラフを投稿したことを通知"""
    emit('all_paragraphs_submitted', room=f'room_{room_id}', namespace='/ws/game')

def broadcast_visibility_update(room_id: int, visibility_state: dict):
    """表示状態の更新をブロードキャスト"""
    emit('visibility_update', {
        'visibility_state': visibility_state
    }, room=f'room_{room_id}', namespace='/ws/game')

def broadcast_game_ended(room_id: int):
    """ゲーム終了を通知"""
    emit('game_ended', {
        'room_id': room_id,
        'redirect_url': f'/room/list'
    }, room=f'room_{room_id}', namespace='/ws/game')

def broadcast_show_next_note(room_id: int, next_note_id: int):
    """次のノートを表示するように通知"""
    emit('show_next_note', {
        'room_id': room_id,
        'next_note_id': next_note_id
    }, room=f'room_{room_id}', namespace='/ws/game')

def init_websocket(socketio):
    @socketio.on('join', namespace='/ws/game')
    def handle_join(data):
        room_id = data.get('room_id')
        if not room_id:
            return

        room = Room.query.get(room_id)
        if not room:
            return

        player = Player.query.filter_by(user_id=current_user.id, room_id=room_id).first()
        if not player:
            return

        join_room(f'room_{room_id}')
        broadcast_title_progress(room_id, room.written_titles_count(), len(room.players))
        
    @socketio.on('set_title', namespace='/ws/game')
    def handle_set_title(data):
        """タイトルを設定"""
        room_id = data.get('room_id')
        title = data.get('title')

        if not all([room_id, title]):
            emit('error', {'message': '必要な情報が不足しています'})
            return
        
        # ノートを取得してタイトルを設定
        notes = Note.query.filter_by(room_id=room_id).all()
        note = next((n for n in notes if n.writers and n.writers[0] == str(current_user.id)), None)
        if note:
            room = Room.query.get(room_id)
            note.title = title
                
            db.session.commit()

            # 進捗状況を取得して通知
            completed_count = room.written_titles_count()
            total_players = len(room.players)
            
            broadcast_title_progress(room_id, completed_count, total_players)

            # 全員がタイトルを設定したら次のページへ
            if completed_count == total_players:
                broadcast_all_titles_set(room_id)
        else:
            emit('error', {'message': 'ノートが見つかりません'})

    @socketio.on('subscribe_game', namespace='/ws/game')
    def handle_subscribe_game(data: dict) -> None:
        """
        ゲームプレイ中のWebSocketチャンネルに参加:
        - room_idに対応するWSチャンネルへjoin
        - 例: クライアントが /game/play ページに入ったとき呼ぶ
        """
        room_id = data.get('room_id')
        if room_id is None:
            emit('error_message', {'error': 'room_id is required'}, to=request.sid)
            return

        room = Room.query.get(room_id)
        if not room:
            emit('error_message', {'error': 'Room not found'}, to=request.sid)
            return

        if room.status != RoomStatus.PLAYING:
            emit('error_message', {'error': 'このルームは現在ゲームプレイ中ではありません'}, to=request.sid)
            return

        join_room(f'room_{room_id}')
        emit('game_subscribed', {'status': 'ok'}, to=request.sid)
        
    @socketio.on('subscribe_result', namespace='/ws/game')
    def handle_subscribe_result(data: dict) -> None:
        """リザルト画面に接続"""
        room_id = data.get('room_id')
        if room_id is None:
            emit('error_message', {'error': 'room_id is required'}, to=request.sid)
            return

        room = Room.query.get(room_id)
        if not room:
            emit('error_message', {'error': 'Room not found'}, to=request.sid)
            return

        if room.status != RoomStatus.PLAYING:
            emit('error_message', {'error': 'このルームは現在ゲームプレイ中ではありません'}, to=request.sid)
            return
        
        join_room(f'room_{room_id}')
        emit('result_connected', {'status': 'ok'}, to=request.sid)
        
    @socketio.on('connect_result', namespace='/ws/game')
    def handle_connect_result(data: dict) -> None:
        """
        リザルト画面に接続するWebSocketイベント
        - 終了したルーム向けにjoin
        """
        room_id = data.get('room_id')
        if room_id is None:
            emit('error_message', {'error': 'room_id is required'}, to=request.sid)
            return

        room = Room.query.get(room_id)
        if not room:
            emit('error_message', {'error': 'Room not found'}, to=request.sid)
            return

        if room.status != RoomStatus.FINISHED:
            emit('error_message', {'error': 'まだゲームは終了していません'}, to=request.sid)
            return

        join_room(f'room_{room_id}')
        emit('result_connected', {'status': 'ok'}, to=request.sid)

    @socketio.on('submit_paragraph', namespace='/ws/game')
    def handle_submit_paragraph(data):
        """パラグラフを投稿"""
        room_id = data.get('room_id')
        note_id = data.get('note_id')
        paragraph = data.get('paragraph')
        is_update = data.get('is_update', False)

        if not all([room_id, note_id, paragraph]):
            emit('error', {'message': '必要な情報が不足しています'})
            return
        
        # ノートを取得してパラグラフを追加
        note: Note = Note.query.get(note_id)
        paragraph = paragraph.replace('\n', '<br>')
        if note and note.room_id == room_id:
            room = Room.query.get(room_id)
            current_turn = room.settings.get('current_turn', 0)
            
            # 既存のパラグラフがある場合は更新
            if is_update and note.contents and len(note.contents) > current_turn:
                new_contents = note.contents.copy()
                new_contents[current_turn] = {
                    'writer_id': str(current_user.id),
                    'paragraph': paragraph,
                    "timestamp": datetime.utcnow().isoformat()
                }
                note.contents = None
                db.session.flush()
                note.contents = new_contents
            else:
                note.add_content(str(current_user.id), paragraph)
                
            db.session.commit()

            # 進捗状況を取得して通知
            completed_count = room.written_paragraphs_count()
            total_players = len(room.players)
            
            broadcast_paragraph_progress(room_id, completed_count, total_players)

            # 全員がパラグラフを投稿したら次のターンへ
            if completed_count == total_players:
                broadcast_all_paragraphs_submitted(room_id)
        else:
            emit('error', {'message': 'ノートが見つかりません'})

    @socketio.on('next_paragraph', namespace='/ws/game')
    def handle_next_paragraph(data):
        """次のパラグラフを表示"""
        room_id = data.get('room_id')
        if not room_id:
            emit('error', {'message': 'room_id is required'})
            return

        room = Room.query.get(room_id)
        if not room:
            emit('error', {'message': 'Room not found'})
            return

        if room.creator_id != current_user.id:
            emit('error', {'message': 'Only room creator can proceed'})
            return

        # 現在の表示状態を取得
        visibility_state = room.get_visibility_state()
        
        # 表示可能な次のパラグラフを探す
        for note_id, paragraphs in visibility_state.items():
            for index, visible in paragraphs.items():
                if not visible:
                    # 表示状態を更新
                    new_settings = dict(room.settings)
                    
                    if 'visibility_state' not in new_settings:
                        new_settings['visibility_state'] = {}
                    if str(note_id) not in new_settings['visibility_state']:
                        new_settings['visibility_state'][str(note_id)] = {}
                    
                    new_settings['visibility_state'][str(note_id)][str(index)] = True
                    
                    # SQLAlchemyの変更検知を確実にするため、一度Noneを設定してから新しい値を設定
                    room.settings = None
                    db.session.flush()
                    room.settings = new_settings
                    db.session.commit()
                    
                    # 更新をブロードキャスト
                    broadcast_visibility_update(room_id, room.get_visibility_state())
                    return

        emit('error', {'message': 'No more paragraphs to show'})

    @socketio.on('end_game', namespace='/ws/game')
    def handle_end_game(data):
        """ゲームを終了"""
        room_id = data.get('room_id')
        if not room_id:
            emit('error', {'message': 'room_id is required'})
            return

        room = Room.query.get(room_id)
        if not room:
            emit('error', {'message': 'Room not found'})
            return

        if room.creator_id != current_user.id:
            emit('error', {'message': 'Only room creator can end the game'})
            return

        # 全てのパラグラフが表示されているか確認
        visibility_state = room.get_visibility_state()
        all_visible = all(
            all(visible for visible in paragraphs.values())
            for paragraphs in visibility_state.values()
        )

        if not all_visible:
            emit('error', {'message': 'Not all paragraphs are visible yet'})
            return

        # ルームをアーカイブ
        room.archive()
        db.session.commit()

        # ゲーム終了を通知
        broadcast_game_ended(room_id)

    @socketio.on('show_next_note', namespace='/ws/game')
    def handle_show_next_note(data):
        """次のノートを表示"""
        room_id = data.get('room_id')
        next_note_id = data.get('next_note_id')

        if not all([room_id, next_note_id]):
            emit('error', {'message': '必要な情報が不足しています'})
            return

        room = Room.query.get(room_id)
        if not room:
            emit('error', {'message': 'Room not found'})
            return

        # 次のノートを表示するように通知
        broadcast_show_next_note(room_id, next_note_id)


