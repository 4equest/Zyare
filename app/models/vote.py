from datetime import datetime
from app.extensions import db
from app.models.room import Room
from app.models.user import User

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    voter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vote1 = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vote2 = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    room = db.relationship('Room', backref=db.backref('votes', lazy=True))
    voter = db.relationship('User', foreign_keys=[voter_id], backref=db.backref('votes_cast', lazy=True))
    voted_user1 = db.relationship('User', foreign_keys=[vote1], backref=db.backref('votes_received1', lazy=True))
    voted_user2 = db.relationship('User', foreign_keys=[vote2], backref=db.backref('votes_received2', lazy=True)) 