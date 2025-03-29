from abc import ABC, abstractmethod
from typing import Dict
from app.models.room import Room

class BaseGameMode(ABC):
    def __init__(self, room: Room) -> None:
        self.room = room

    @abstractmethod
    def validate_paragraph(self, paragraph: str) -> bool:
        pass

    @abstractmethod
    def is_game_over(self) -> bool:
        pass

    @abstractmethod
    def calculate_results(self) -> Dict:
        pass
