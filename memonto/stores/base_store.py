from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict


class StoreModel(BaseModel, ABC):
    name: str = ...
    model_config = ConfigDict(arbitrary_types_allowed=True)

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