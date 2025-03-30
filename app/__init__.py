# app/__init__.py

import os
from flask import Flask
from config import Config
from app.extensions import db, migrate, login_manager, socketio

def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), "templates")
    )
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)

    # マイグレーション初期化(既に migrations/ ディレクトリがある前提)
    migrate.init_app(app, db)

    # Blueprint登録(既存の実装例)
    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.room.routes import room_bp
    from app.blueprints.game.routes import game_bp
    from app.blueprints.main.routes import main_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(room_bp, url_prefix='/room')
    app.register_blueprint(game_bp, url_prefix='/game')
    app.register_blueprint(main_bp, url_prefix='/')
    
    from app.blueprints.room.websockets import init_websocket as room_init_websocket
    from app.blueprints.game.websockets import init_websocket as game_init_websocket

    room_init_websocket(socketio)
    game_init_websocket(socketio)

    with app.app_context():
        from app.models import User, Player, Room, Note
        db.create_all()  # テーブル作成
        # BOTユーザーの初期化
        User.initialize_bots()
    return app
