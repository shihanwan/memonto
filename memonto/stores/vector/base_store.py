from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict


class VectorStoreModel(BaseModel, ABC):
    name: str = ...
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @abstractmethod
    def save(self):
        """
        Persist the current memory to the datastore.
        """
        pass

    @abstractmethod
    def search(self):
        """
        Perform a get query against the datastore for memory data.
        """
        pass
