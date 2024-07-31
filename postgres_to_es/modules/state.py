import abc
import json
from typing import Any


class BaseStorage:
    @abc.abstractmethod
    def save_state(self, state: dict) -> None:
        """Сохранить состояние в постоянное хранилище"""
        pass

    @abc.abstractmethod
    def retrieve_state(self) -> dict:
        """Загрузить состояние локально из постоянного хранилища"""
        pass


class JsonFileStorage(BaseStorage):
    def __init__(self, file_path: str | None):
        self.file_path = file_path

    def save_state(self, state: dict) -> None:
        with open(self.file_path, "w") as file:
            json.dump(state, file)

    def retrieve_state(self) -> dict:
        try:
            with open(self.file_path, "r") as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}
        return data or {}


class State:
    def __init__(self, storage: BaseStorage):
        self.storage = storage

    def set_state(self, key: str, value: Any) -> None:
        self.storage.save_state(state={key: value})

    def get_state(self, key: str) -> Any:
        data = self.storage.retrieve_state()
        return data.get(key)
