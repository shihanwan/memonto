import requests
from rdflib import Graph

from memonto.stores.base_store import StoreModel


class ApacheJena(StoreModel):
    name: str = "apache_jena"
    connection_url: str = ...
    username: str = None
    password: str = None

    def save(self, g: Graph) -> None:
        rdf_data = g.serialize(format="nt")

        sparql_update_query = f"INSERT DATA {{{rdf_data}}}"

        print(sparql_update_query)

        response = requests.post(
            self.connection_url,
            data=sparql_update_query,
            headers={"Content-Type": "application/sparql-update"},
        )

        print(response.text)
