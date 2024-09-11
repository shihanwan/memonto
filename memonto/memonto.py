from pydantic import BaseModel, Field, model_validator
from rdflib import Graph, Namespace
from typing import Optional, Union

from memonto.llms.base_llm import LLMModel
from memonto.llms.factory import llm_factory
from memonto.core.commit import commit_memory
from memonto.core.graph import graph_memory

class Memonto(BaseModel):
    g: Graph = Field(..., description="An RDF graph representing the ontology of the memory.")
    EX: Namespace = Field(..., description="A namespace for the entities in the memory ontology.")
    llm_provider: str = Field(..., description="The name of the LLM provider.")
    llm: Optional[LLMModel] = Field(None, description="Model instance.")

    @model_validator(mode="after")
    def init(self) -> "Memonto":
        self.llm = llm_factory(self.llm_provider)
        return self

    def commit(self, query: str) -> None:
        """
        Break down user query into memory that fits on the RDF ontology.

        :param query: The user query that is broken down into a graph then committed to memory.

        :return: None
        """
        return commit_memory(g=self.g, EX=self.EX, llm=self.llm, query=query)

    def graph(self, format: str = "turtle") -> Union[str, dict]:
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