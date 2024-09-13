from rdflib import Graph, URIRef, Literal
from SPARQLWrapper import SPARQLWrapper, POST

from memonto.stores.base_store import StoreModel


class ApacheJena(StoreModel):
    name: str = "apache_jena"
    connection_url: str = ...
    username: str = None
    password: str = None

    def _query(
        self,
        method: Literal["POST"],
        query: str,
        return_format: str,
    ) -> SPARQLWrapper:
        sparql = SPARQLWrapper(self.connection_url)
        sparql.setQuery(query)
        sparql.setMethod(method)

        if self.username and self.password:
            sparql.setCredentials(self.username, self.password)

        sparql.setReturnFormat(return_format)

        try:
            return sparql.query()
        except Exception as e:
            print(f"SPARQL query error: {e}")

    def save(self, g: Graph) -> None:
        rdf_data = g.serialize(format="nt")
        query = f"INSERT DATA {{{rdf_data}}}"

        self._query(
            method=POST,
            query=query,
            return_format="json",
        )

    def load(self) -> Graph:
        query = "SELECT ?s ?p ?o WHERE {?s ?p ?o}"

        response = self._query(
            method=POST,
            query=query,
            return_format="json",
        )

        g = Graph()

        for binding in response["results"]["bindings"]:
            subj = URIRef(binding["s"]["value"])
            pred = URIRef(binding["p"]["value"])
            if binding["o"]["type"] == "uri":
                obj = URIRef(binding["o"]["value"])
            else:
                obj = Literal(binding["o"]["value"])

            g.add((subj, pred, obj))

        return g
