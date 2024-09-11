from pydantic import BaseModel, Field
from rdflib import Graph, Namespace
from typing import Union

from memonto.core.graph import graph_memory
from memonto.core.commit import commit_memory

class Memonto(BaseModel):
    g: Graph = Field(..., description="An RDF graph representing the ontology of the memory.")
    EX: Namespace = Field(..., description="A namespace for the entities in the memory ontology.")
    
    def commit(self, query: str) -> None:
        """
        Simulate committing memory data.
        """
        return commit_memory(g=self.g, EX=self.EX, query=query)

    def graph(self, format: str = "turtle") -> Union[str, dict]:
        """
        Return a text representation of the memory ontology.
        
        Parameters:
        format (str): The format in which to render the graph. Supported formats are:
            - "turtle": Return the graph in Turtle format.
            - "json": Return the graph in JSON-LD format.
        
        Returns:
        Union[str, dict]: A text representation of the memory ontology. 
            - "turtle" format returns a string in Turtle format.
            - "json" format returns a dictionary in JSON-LD format.
        """
        return graph_memory(g=self.g, format=format)

    class Config:
        arbitrary_types_allowed = True