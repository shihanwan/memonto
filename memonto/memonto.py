from pydantic import BaseModel, Field
from rdflib import Graph
from typing import Union

from memonto.graph import graph_memory

class Memonto(BaseModel):
    g: Graph = Field(..., description="An RDF graph representing the ontology of the memory.")

    def commit(self):
        """
        Simulate committing memory data.
        """
        print(f"Committing memory using RDF graph with {len(self.g)} triples.")

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