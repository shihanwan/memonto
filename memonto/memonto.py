from pydantic import BaseModel, Field, model_validator
from rdflib import Graph, Namespace
from typing import Optional, Union

from memonto.core.commit import commit_memory
from memonto.core.configure import configure
from memonto.core.fetch import fetch_memory
from memonto.core.graph import graph_memory
from memonto.llms.base_llm import LLMModel
from memonto.llms.factory import llm_factory
from memonto.stores.base_store import StoreModel
from memonto.stores.factory import store_factory


class Memonto(BaseModel):
    g: Graph = Field(
        ...,
        description="An RDF graph representing the ontology of the memory.",
    )
    EX: Namespace = Field(
        ...,
        description="A namespace for the entities in the memory ontology.",
    )
    llm: Optional[LLMModel] = Field(None, description="Model instance.")
    store: Optional[StoreModel] = Field(None, description="Store instance.")
    
    def configure(self, config: dict) -> None:
        """
        Configure memonto with the desired llm model and datastore.

        :param config: A dictionary containing the configuration for the LLM model and the store.
            configs = {
                "store": {
                    "provider": "apache_jena",
                    "config": {
                        "connection_url": "http://localhost:3030/ds/update",
                        "username": "",
                        "password": "",
                    },
                },
                "model": {
                    "provider": "openai",
                    "config": {
                        "model": "gpt-4o",
                        "api_key": "",
                    },
                }
            }

        :return: None
        """
        return configure(self, config=config)

    def commit(self, query: str) -> None:
        """
        Break down user query into memory that fits on the RDF ontology.

        :param query: The user query that is broken down into a graph then committed to memory.

        :return: None
        """
        return commit_memory(g=self.g, EX=self.EX, llm=self.llm, query=query)

    def fetch(self) -> str:
        """
        Return a text summary of the current memory.

        :return: A text summary of the current memory.
        """
        return fetch_memory(g=self.g, llm=self.llm)

    def render(self, format: str = "turtle") -> Union[str, dict]:
        """
        Return a text representation of the memory ontology.

        :param format: The format in which to render the graph. Supported formats are:
            - "turtle": Return the graph in Turtle format.
            - "json": Return the graph in JSON-LD format.

        :return: A text representation of the memory ontology.
            - "turtle" format returns a string in Turtle format.
            - "json" format returns a dictionary in JSON-LD format.
        """
        return graph_memory(g=self.g, format=format)

    class Config:
        arbitrary_types_allowed = True
