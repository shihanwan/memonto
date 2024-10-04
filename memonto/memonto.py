import asyncio
from pydantic import BaseModel, ConfigDict, Field, model_validator
from rdflib import Graph, Namespace, URIRef
from typing import Optional

from memonto.core.configure import _configure
from memonto.core.init import init
from memonto.core.forget import _forget
from memonto.core.retrieve import _retrieve
from memonto.core.recall import _recall
from memonto.core.remember import _remember
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
    ephemeral: Optional[bool] = False
    debug: Optional[bool] = False
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def init(self) -> "Memonto":
        init(debug=self.debug)
        return self

    def configure(self, config: dict) -> None:
        """
        Configure memonto with the desired llm model and data stores.

        :param config: A dictionary containing the configuration for the LLM model and the data stores.

        :return: None
        """
        self.triple_store, self.vector_store, self.llm = _configure(config=config)

    @require_config("llm", "triple_store")
    def retain(self, message: str) -> None:
        """
        Analyze a text for relevant information that maps onto an RDF ontology then add them to the memory store.

        :param message: The user message that is broken down into a graph then committed to memory.

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
    def recall(self, context: str = None) -> str:
        """
        Return a text summary of either all or only relevant memories currently in the memory store. In ephemeral mode, a summary of all memories will be returned.

        :param context[Optional]: Context to query the memory store for relevant memories only.

        :return: A text summary of the memory.
        """
        return _recall(
            data=self.data,
            llm=self.llm,
            triple_store=self.triple_store,
            vector_store=self.vector_store,
            context=context,
            id=self.id,
            ephemeral=self.ephemeral,
        )

    @require_config("llm", "triple_store", "vector_store")
    async def arecall(self, context: str = None) -> str:
        return await asyncio.to_thread(
            _recall,
            data=self.data,
            llm=self.llm,
            triple_store=self.triple_store,
            vector_store=self.vector_store,
            context=context,
            id=self.id,
            ephemeral=self.ephemeral,
        )

    @require_config("triple_store")
    def retrieve(self, uri: URIRef = None, query: str = None) -> list:
        """
        Query against the memory store to retrieve raw memory data rather than a text summary. Raw queries are not supported in ephemeral mode since there are no data stores.

        :param uri[Optional]: URI of the entity to query for.
        :param query[Optional]: Raw query that will be performed against the memory store. If you pass in a raw query then uri will be ignored.

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

        :return: None.
        """
        self.ontology, self.data = _remember(
            namespaces=self.namespaces,
            triple_store=self.triple_store,
            id=self.id,
        )
