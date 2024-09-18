from abc import ABC, abstractmethod
from pydantic import BaseModel


class StoreModel(BaseModel, ABC):
    name: str = ...

    @abstractmethod
    def save(self) -> None:
        """
        Persist the current memory to the datastore.
        """
        pass

    @abstractmethod
    def load(self) -> None:
        """
        Load existing memory from datastore.
        """
        pass

    @abstractmethod
    def get(self) -> None:
        """
        Perform a get query against the datastore for memory data.
        """
        pass

    class Config:
        arbitrary_types_allowed = True
