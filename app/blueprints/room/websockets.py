from flask import current_app, request
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app.extensions import socketio, db
from app.models.room import Room, RoomStatus
from app.models.player import Player

def _broadcast_player_list(room_id: int):
    """プレイヤー一覧を更新"""
    room = Room.query.get(room_id)
    if not room:
        return

    players = [{
        'user_id': p.user_id,
        'nickname': p.nickname,
        'is_ready': p.is_ready
    } for p in room.players]

    emit('message', {
        'type': 'player_list',
        'players': players
    }, room=f'room_{room_id}', namespace='/ws/room')

def _broadcast_room_settings(room_id: int):
    """ルーム設定を更新"""
    room = Room.query.get(room_id)
    if not room:
        return

    emit('message', {
        'type': 'room_settings',
        'settings': room.settings
    }, room=f'room_{room_id}', namespace='/ws/room')

def _broadcast_game_start(room_id: int):
    """ゲーム開始を通知"""
    room = Room.query.get(room_id)
    if not room:
        return

    emit('game_started', {
        'room_id': room_id,
        'redirect_url': f'/game/set_title/{room_id}'
    }, room=f'room_{room_id}', namespace='/ws/room')

def init_websocket(socketio):
    @socketio.on('connect', namespace='/ws/room')
    def handle_connect():
        if not current_user.is_authenticated:
            return False

    @socketio.on('join', namespace='/ws/room')
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
        _broadcast_player_list(room_id)
        _broadcast_room_settings(room_id)

    @socketio.on('disconnect', namespace='/ws/room')
    def handle_disconnect():
        # 必要に応じてクリーンアップ処理を追加
        pass

    @socketio.on('leave_room_event', namespace='/ws/room')
    def handle_leave_room(data: dict) -> None:
        """
        WebSocketイベント: クライアントがルームから離脱(WS退出)
        """
        room_id = data.get('room_id')
        if room_id is None:
            emit('error_message', {'error': 'room_id is required'}, to=request.sid, namespace='/ws/room')
            return

        room = Room.query.get(room_id)
        if not room:
            emit('error_message', {'error': 'Room not found'}, to=request.sid, namespace='/ws/room')
            return

        leave_room(f'room_{room_id}')
        _broadcast_player_list(room_id)
