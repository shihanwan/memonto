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

    class Config:
        arbitrary_types_allowed = True