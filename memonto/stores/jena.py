from rdflib import Graph, URIRef, Literal
from SPARQLWrapper import SPARQLWrapper, POST, JSON

from memonto.stores.base_store import StoreModel


class ApacheJena(StoreModel):
    name: str = "apache_jena"
    connection_url: str = ...
    username: str = None
    password: str = None

    def _query(
        self,
        url: str,
        method: Literal,
        query: str,
        return_format: str = JSON,
    ) -> SPARQLWrapper:
        sparql = SPARQLWrapper(url)
        sparql.setQuery(query)
        sparql.setMethod(method)

        if self.username and self.password:
            sparql.setCredentials(self.username, self.password)

        sparql.setReturnFormat(return_format)

        try:
            return sparql.query().convert()
        except Exception as e:
            print(f"SPARQL query error: {e}")

    def save(self, g: Graph, id: str = None) -> None:
        rdf_data = g.serialize(format="nt")

        if id:
            query = f"INSERT DATA {{ GRAPH <{id}> {{{rdf_data}}} }}"
        else:
            query = f"INSERT DATA {{{rdf_data}}}"

        self._query(
            url=f"{self.connection_url}/update",
            method=POST,
            query=query,
        )

        print(g.serialize(format="turtle"))

    def load(self, id: str = None) -> Graph:
        if id:
            query = f"SELECT ?s ?p ?o WHERE {{ GRAPH <{id}> {{ ?s ?p ?o }} }}"
        else:
            query = "SELECT ?s ?p ?o WHERE { ?s ?p ?o }"

        response = self._query(
            url=f"{self.connection_url}/sparql",
            method=POST,
            query=query,
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

        print(g.serialize(format="turtle"))

        return g
