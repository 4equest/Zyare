from abc import ABC, abstractmethod
from typing import Dict
from app.models.room import Room

class BaseGameMode(ABC):
    @staticmethod
    @abstractmethod
    def validate_paragraph(room: Room, paragraph: str) -> bool:
        pass

    @staticmethod
    @abstractmethod
    def is_game_over(room: Room) -> bool:
        pass

    @staticmethod
    @abstractmethod
    def calculate_results(room: Room) -> Dict:
        pass
