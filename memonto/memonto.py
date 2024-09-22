from pydantic import BaseModel, ConfigDict, Field 
from rdflib import Graph, Namespace, URIRef
from typing import Optional, Union

from memonto.core.commit import commit_memory
from memonto.core.configure import configure
from memonto.core.fetch import fetch_memory
from memonto.core.graph import render_memory
from memonto.core.remember import load_memory
from memonto.core.query import query_memory_store
from memonto.llms.base_llm import LLMModel
from memonto.stores.base_store import StoreModel


class Memonto(BaseModel):
    g: Graph = Field(..., description="An RDF graph representation of memories.")
    # TODO: support multiple namespaces
    n: Namespace = Field(..., description="Am RDF namespace for the memory.")
    llm: Optional[LLMModel] = Field(None, description="LLM model instance.")
    store: Optional[StoreModel] = Field(None, description="Datastore instance.")
    debug: Optional[bool] = Field(False, description="Enable debug mode.")
    auto_expand: Optional[bool] = Field(
        False, description="Enable automatic expansion of the ontology."
    )
    auto_forget: Optional[bool] = Field(
        False, description="Enable automatic forgetting of memories."
    )
    model_config = ConfigDict(arbitrary_types_allowed=True)

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

    def retain(self, query: str, id: str = None) -> None:
        """
        Analyze a text for relevant information that maps onto an RDF ontology then commit them to the memory store.

        :param query: The user query that is broken down into a graph then committed to memory.
        :param id[Optional]: Unique identifier for a memory. Often associated with a unique transaction or user.

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
            expand_ontology=self.auto_expand,
        )

    def remember(self, id: str = None) -> None:
        """
        Load existing memories from the memory store to a memonto instance.

        :param id[Optional]: Unique identifier for a memory. Often associated with a unique transaction or user.

        :return: None.
        """
        self.g = load_memory(store=self.store, id=id)

    def retrieve(self) -> str:
        """
        Return a text summary of all memories currently stored in the memory store.

        :return: A text summary of the entire current memory.
        """
        return fetch_memory(g=self.g, llm=self.llm)

    def recall(self):
        """
        Return a text summary of partial memories that are relevant to a context.
        """
        pass

    def forget(self):
        """
        Remove memories from the memory store.
        """
        pass

    def query(self, id: str = None, uri: URIRef = None, query: str = None) -> list:
        """
        Perform query against the memory store to retrieve raw memory data rather than a summary.

        :param id[Optional]: Unique identifier for a memory. Often associated with a unique transaction or user.
        :param uri[Optional]: URI of the entity to query for.
        :param query[Optional]: Raw query that will be performed against the datastore. If you pass in a raw query then the id and uri parameters will be ignored.

        :return: A list of triples (subject, predicate, object).
        """
        return query_memory_store(store=self.store, id=id, uri=uri, query=query)

    def render(self, format: str = "turtle") -> Union[str, dict]:
        """
        Return a text representation of the entire currently stored memory.

        :param format: The format in which to render the graph. Supported formats are:
            - "turtle": Return the graph in Turtle format.
            - "json": Return the graph in JSON-LD format.
            - "text": Return the graph in text format.
            - "image": Return the graph as a png image.

        :return: A text representation of the memory.
            - "turtle" format returns a string in Turtle format.
            - "json" format returns a dictionary in JSON-LD format.
            - "text" format returns a string in text format.
            - "image" format returns a string with the path to the png image.
        """
        return render_memory(g=self.g, format=format)
