import asyncio
from pydantic import BaseModel, ConfigDict, Field, model_validator
from rdflib import Graph, Namespace, URIRef
from typing import Optional, Union

from memonto.core.configure import _configure
from memonto.core.init import init
from memonto.core.forget import _forget
from memonto.core.retrieve import _retrieve
from memonto.core.recall import _recall
from memonto.core.remember import _remember
from memonto.core.render import _render
from memonto.core.retain import _retain
from memonto.llms.base_llm import LLMModel
from memonto.stores.triple.base_store import TripleStoreModel
from memonto.stores.vector.base_store import VectorStoreModel
from memonto.utils.decorators import require_config


class Memonto(BaseModel):
    id: Optional[str] = None
    ontology: Graph = ...
    namespaces: dict[str, Namespace] = ...
    data: Graph = Field(..., default_factory=Graph)
    llm: Optional[LLMModel] = None
    triple_store: Optional[TripleStoreModel] = None
    vector_store: Optional[VectorStoreModel] = None
    auto_expand: Optional[bool] = False
    auto_forget: Optional[bool] = False
    ephemeral: Optional[bool] = False
    debug: Optional[bool] = False
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
        self.triple_store, self.vector_store, self.llm = _configure(config=config)

    @require_config("llm", "triple_store")
    def retain(self, message: str) -> None:
        """
        Analyze a text for relevant information that maps onto an RDF ontology then commit them to the memory store.

        :param query: The user query that is broken down into a graph then committed to memory.
        :param id[Optional]: Unique identifier for a memory. Often associated with a unique transaction or user.

        :return: None
        """
        return _retain(
            ontology=self.ontology,
            namespaces=self.namespaces,
            data=self.data,
            llm=self.llm,
            triple_store=self.triple_store,
            vector_store=self.vector_store,
            message=message,
            id=self.id,
            auto_expand=self.auto_expand,
            ephemeral=self.ephemeral,
        )

    @require_config("llm", "triple_store")
    async def aretain(self, message: str) -> None:
        return await asyncio.to_thread(
            _retain,
            ontology=self.ontology,
            namespaces=self.namespaces,
            data=self.data,
            llm=self.llm,
            triple_store=self.triple_store,
            vector_store=self.vector_store,
            message=message,
            id=self.id,
            auto_expand=self.auto_expand,
            ephemeral=self.ephemeral,
        )

    @require_config("llm", "triple_store", "vector_store")
    def recall(self, message: str = None) -> str:
        """
        Return a text summary of all memories currently stored in context.

        :return: A text summary of the entire current memory.
        """
        return _recall(
            data=self.data,
            llm=self.llm,
            triple_store=self.triple_store,
            vector_store=self.vector_store,
            message=message,
            id=self.id,
            ephemeral=self.ephemeral,
        )

    @require_config("llm", "triple_store", "vector_store")
    async def arecall(self, message: str = None) -> str:
        return await asyncio.to_thread(
            _recall,
            data=self.data,
            llm=self.llm,
            triple_store=self.triple_store,
            vector_store=self.vector_store,
            message=message,
            id=self.id,
            ephemeral=self.ephemeral,
        )

    @require_config("triple_store")
    def retrieve(self, uri: URIRef = None, query: str = None) -> list:
        """
        Perform query against the memory store to retrieve raw memory data rather than a summary.

        :param id[Optional]: Unique identifier for a memory. Often associated with a unique transaction or user.
        :param uri[Optional]: URI of the entity to query for.
        :param query[Optional]: Raw query that will be performed against the datastore. If you pass in a raw query then the id and uri parameters will be ignored.

        :return: A list of triples (subject, predicate, object).
        """
        return _retrieve(
            ontology=self.ontology,
            data=self.data,
            triple_store=self.triple_store,
            id=self.id,
            uri=uri,
            query=query,
            ephemeral=self.ephemeral,
        )

    @require_config("triple_store")
    async def aretrieve(self, uri: URIRef = None, query: str = None) -> list:
        return await asyncio.to_thread(
            _retrieve,
            ontology=self.ontology,
            data=self.data,
            triple_store=self.triple_store,
            id=self.id,
            uri=uri,
            query=query,
            ephemeral=self.ephemeral,
        )

    def forget(self) -> None:
        """
        Remove memories from the memory store.
        """
        return _forget(
            data=self.data,
            id=self.id,
            triple_store=self.triple_store,
            vector_store=self.vector_store,
            ephemeral=self.ephemeral,
        )

    async def aforget(self) -> None:
        await asyncio.to_thread(
            _forget,
            data=self.data,
            id=self.id,
            triple_store=self.triple_store,
            vector_store=self.vector_store,
            ephemeral=self.ephemeral,
        )

    # TODO: no longer needed, can be deprecated or removed
    @require_config("triple_store")
    def remember(self) -> None:
        """
        Load existing memories from the memory store to a memonto instance.

        :param id[Optional]: Unique identifier for a memory. Often associated with a unique transaction or user.

        :return: None.
        """
        self.ontology, self.data = _remember(
            namespaces=self.namespaces,
            triple_store=self.triple_store,
            id=self.id,
        )

    def _render(
        self,
        format: str = "turtle",
        path: str = None,
    ) -> Union[str, dict]:
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
        return _render(g=self.data, format=format, path=path)
