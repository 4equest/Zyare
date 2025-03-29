# app/blueprints/room/__init__.py

from flask import Blueprint

room_bp = Blueprint('room', __name__)

from . import routes
from . import websockets
