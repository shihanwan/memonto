from pydantic import BaseModel, ConfigDict, Field, model_validator
from rdflib import Graph, Namespace, URIRef
from typing import Optional, Union

from memonto.core.configure import configure
from memonto.core.init import init
from memonto.core.query import query_memory_data
from memonto.core.remember import load_memory
from memonto.core.render import render_memory
from memonto.core.retain import retain_memory
from memonto.core.retrieve import recall_memory
from memonto.llms.base_llm import LLMModel
from memonto.stores.triple.base_store import TripleStoreModel
from memonto.stores.vector.base_store import VectorStoreModel


class Memonto(BaseModel):
    id: Optional[str] = Field(None, description="Unique identifier for a memory group.")
    ontology: Graph = Field(..., description="Schema describing the memory ontology.")
    namespaces: dict[str, Namespace] = Field(
        ..., description="Namespaces used in the memory ontology."
    )
    data: Graph = Field(
        default_factory=Graph, description="Data graph containing the actual memories."
    )
    llm: Optional[LLMModel] = Field(None, description="LLM model instance.")
    triple_store: Optional[TripleStoreModel] = Field(None, description="Store triples.")
    vector_store: Optional[VectorStoreModel] = Field(None, description="Store vectors.")
    debug: Optional[bool] = Field(False, description="Enable debug mode.")
    auto_expand: Optional[bool] = Field(
        False, description="Enable automatic expansion of the ontology."
    )
    auto_forget: Optional[bool] = Field(
        False, description="Enable automatic forgetting of memories."
    )
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def init(self) -> "Memonto":
        init(debug=self.debug)
        return self

    def configure(self, config: dict) -> None:
        """
        Configure memonto with the desired llm model and datastore.

        :param config: A dictionary containing the configuration for the LLM model and the store.
            configs = {
                "triple_store": {
                    "provider": "apache_jena",
                    "config": {
                        "connection_url": "http://localhost:3030/ds/update",
                        "username": "",
                        "password": "",
                    },
                },
                "vector_store": {
                    "provider": "chroma",
                    "config": {
                        "mode": "local",
                        "path": ".local/",
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
        self.triple_store, self.vector_store, self.llm = configure(config=config)

    def retain(self, message: str) -> None:
        """
        Analyze a text for relevant information that maps onto an RDF ontology then commit them to the memory store.

        :param query: The user query that is broken down into a graph then committed to memory.
        :param id[Optional]: Unique identifier for a memory. Often associated with a unique transaction or user.

        :return: None
        """
        return retain_memory(
            ontology=self.ontology,
            namespaces=self.namespaces,
            data=self.data,
            llm=self.llm,
            triple_store=self.triple_store,
            vector_store=self.vector_store,
            message=message,
            id=self.id,
            debug=self.debug,
            auto_expand=self.auto_expand,
        )

    def recall(self, message: str = None) -> str:
        """
        Return a text summary of all memories currently stored in context.

        :return: A text summary of the entire current memory.
        """
        return recall_memory(
            llm=self.llm,
            triple_store=self.triple_store,
            vector_store=self.vector_store,
            message=message,
            id=self.id,
            debug=self.debug,
        )

    def remember(self) -> None:
        """
        Load existing memories from the memory store to a memonto instance.

        :param id[Optional]: Unique identifier for a memory. Often associated with a unique transaction or user.

        :return: None.
        """
        self.ontology, self.data = load_memory(
            namespaces=self.namespaces,
            store=self.triple_store,
            id=self.id,
            debug=self.debug,
        )

    def forget(self):
        """
        Remove memories from the memory store.
        """
        pass

    def query(self, uri: URIRef = None, query: str = None) -> list:
        """
        Perform query against the memory store to retrieve raw memory data rather than a summary.

        :param id[Optional]: Unique identifier for a memory. Often associated with a unique transaction or user.
        :param uri[Optional]: URI of the entity to query for.
        :param query[Optional]: Raw query that will be performed against the datastore. If you pass in a raw query then the id and uri parameters will be ignored.

        :return: A list of triples (subject, predicate, object).
        """
        return query_memory_data(
            ontology=self.ontology,
            store=self.triple_store,
            id=self.id,
            uri=uri,
            query=query,
            debug=self.debug,
        )

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
        return render_memory(g=self.data, format=format)
