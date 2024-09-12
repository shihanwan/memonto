import requests
from rdflib import Graph

from memonto.stores.base_store import StoreModel


class ApacheJena(StoreModel):
    name: str = "apache_jena"
    connection_url: str = ...
    username: str = None
    password: str = None

    def save(self, g: Graph) -> None:
        rdf_data = g.serialize(format="turtle")
        
        sparql_update_query = f"""
        INSERT DATA {{
            {rdf_data}
        }}
        """
        
        response = requests.post(
            self.connection_url,
            data={"update": sparql_update_query},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            print("RDF graph successfully saved to Apache Jena Fuseki.")
        else:
            print(f"Failed to save RDF graph. Status code: {response.status_code}")