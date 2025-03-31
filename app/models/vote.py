from datetime import datetime
from app.extensions import db
from app.models.room import Room
from app.models.user import User

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    voter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    votes = db.Column(db.JSON, nullable=False)  # 投票対象のユーザーIDの配列
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    room = db.relationship('Room', backref=db.backref('votes', lazy=True))
    voter = db.relationship('User', foreign_keys=[voter_id], backref=db.backref('votes_cast', lazy=True)) 