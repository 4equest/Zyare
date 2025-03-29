# app/models/player.py
from app.extensions import db

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    nickname = db.Column(db.String(64), nullable=False)
    is_ready = db.Column(db.Boolean, default=False, nullable=False)
