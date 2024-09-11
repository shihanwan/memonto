from pydantic import BaseModel, Field
from rdflib import Graph
from typing import Optional

class Memonto(BaseModel):
    g: Graph = Field(..., description="An RDF graph representing the ontology of the memory.")

    def commit(self):
        """
        Simulate committing memory data.
        """
        print(f"Committing memory using RDF graph with {len(self.g)} triples.")

    def graph(self, type: str = "turtle") -> str:
        """
        Return a text representation of the memory ontology.
        
        Parameters:
        type (str): The format in which to render the graph. Supported formats are:
            - 'json': Return the graph in JSON-LD format.
            - 'turtle': Return the graph in Turtle format.
        
        Returns:
        str: text representation of the memory ontology.
        """
        if type == "turtle":
            return self.g.serialize(format="turtle")
        elif type == "json":
            return self.g.serialize(format="json-ld")
        else:
            raise ValueError(f"Unsupported type '{type}'. Choose from 'json', or 'turtle'.")

    class Config:
        arbitrary_types_allowed = True