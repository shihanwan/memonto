from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict


class TripleStoreModel(BaseModel, ABC):
    name: str = ...
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @abstractmethod
    def save(self):
        """
        Persist the current memory to the datastore.
        """
        pass

    @abstractmethod
    def load(self):
        """
        Load existing memory from datastore.
        """
        pass

    @abstractmethod
    def get(self):
        """
        Perform a get query against the datastore for memory data.
        """
        pass

    @abstractmethod
    def get_all(self, graph_id: str = None) -> str:
        """
        Get all memory data from the datastore.

        :param graph_id: The id of the graph to get all memory data from.

        :return: A string representation of the memory data.
        """
        pass

    @abstractmethod
    def query(self):
        """
        Perform a raw query against the datastore for memory data.
        """
        pass
