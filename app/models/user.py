from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    id = db.Column(db.String(50), primary_key=True)
    password_hash = db.Column(db.String(128), nullable=False)

    players = db.relationship("Player", backref="user", lazy=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

from app.extensions import login_manager

@login_manager.user_loader
def load_user(user_id: str) -> User:
    return User.query.get(user_id)
