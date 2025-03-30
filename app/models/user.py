from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.helper import random_hiragana
from sqlalchemy.orm import Mapped
class User(db.Model, UserMixin):
    id = db.Column(db.String(50), primary_key=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_bot: Mapped[bool] = db.Column(db.Boolean, default=False)  # BOTかどうかを示すフラグ

    players = db.relationship("Player", backref="user", lazy=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @classmethod
    def initialize_bots(cls):
        """BOTユーザーを初期化する"""
        for i in range(3):  # bot_0からbot_2まで
            bot_id = f"bot_{i}"
            bot = cls.query.get(bot_id)
            if not bot:
                bot = cls(
                    id=bot_id,
                    password_hash=generate_password_hash(f"bot_password_{i}"),  # パスワードは使用しない
                    is_bot=True
                )
                db.session.add(bot)
        db.session.commit()

from app.extensions import login_manager

@login_manager.user_loader
def load_user(user_id: str) -> User:
    return User.query.get(user_id)
