from pydantic import BaseModel, Field, model_validator
from rdflib import Graph, Namespace
from typing import Optional, Union

from memonto.core.commit import commit_memory
from memonto.core.configure import configure
from memonto.core.fetch import fetch_memory
from memonto.core.graph import render_memory
from memonto.llms.base_llm import LLMModel
from memonto.stores.base_store import StoreModel


class Memonto(BaseModel):
    g: Graph = Field(
        ...,
        description="An RDF graph representing the ontology of the memory.",
    )
    n: Namespace = Field(
        ...,
        description="A namespace for the memory ontology.",
    )
    llm: Optional[LLMModel] = Field(None, description="Model instance.")
    store: Optional[StoreModel] = Field(None, description="Store instance.")
    debug: Optional[bool] = Field(False, description="Flag to enable debug mode.")
    expand_ontology: Optional[bool] = Field(
        False,
        description="Flag to enable automatic expansion of the ontology.",
    )

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

    def commit(self, query: str, id: str = None) -> None:
        """
        Break down the user's query for relevant information that maps onto an RDF ontology and store them as memories.

        :param query: The user query that is broken down into a graph then committed to memory.
        :param id[Optional]: Identifier to track the memory associated with a unique transaction or user.

        :return: None
        """
        return commit_memory(
            g=self.g,
            n=self.n,
            llm=self.llm,
            store=self.store,
            query=query,
            id=id,
            debug=self.debug,
            expand_ontology=self.expand_ontology,
        )

    def fetch(self, id: str = None) -> str:
        """
        Return a text summary of the current memory.

        :param id[Optional]: Identifier to return just the memory associated with a unique transaction or user.

        :return: A text summary of the current memory.
        """
        return fetch_memory(self, llm=self.llm, store=self.store, id=id)

    def render(self, format: str = "turtle") -> Union[str, dict]:
        """
        Return a text representation of the memory ontology.

        :param format: The format in which to render the graph. Supported formats are:
            - "turtle": Return the graph in Turtle format.
            - "json": Return the graph in JSON-LD format.
            - "text": Return the graph in text format.
            - "image": Return the graph as a png image.

        :return: A text representation of the memory ontology.
            - "turtle" format returns a string in Turtle format.
            - "json" format returns a dictionary in JSON-LD format.
            - "text" format returns a string in text format.
            - "image" format returns a string with the path to the png image.
        """
        return render_memory(g=self.g, format=format)

    class Config:
        arbitrary_types_allowed = True
