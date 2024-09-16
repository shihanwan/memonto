from rdflib import Graph, Literal, Namespace, URIRef
from SPARQLWrapper import SPARQLWrapper, POST, TURTLE

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
        format: str = TURTLE,
    ) -> SPARQLWrapper:
        sparql = SPARQLWrapper(url)
        sparql.setQuery(query)
        sparql.setMethod(method)
        sparql.setReturnFormat(format)

        if self.username and self.password:
            sparql.setCredentials(self.username, self.password)

        try:
            return sparql.query().convert()
        except Exception as e:
            print(f"SPARQL query error: {e}")

    def _get_prefixes(self, g: Graph):
        gt = g.serialize(format="turtle")
        return [line for line in gt.splitlines() if line.startswith("@prefix")]

    def save(self, g: Graph, id: str = None) -> None:
        triples = g.serialize(format="nt")
        prefixes = self._get_prefixes(g)
        prefix_block = (
            "\n".join(prefixes).replace("@prefix", "PREFIX").replace(" .", "")
        )

        if id:
            query = f"{prefix_block} INSERT DATA {{ GRAPH <{id}> {{{triples}}} }}"
        else:
            query = f"{prefix_block} INSERT DATA {{{triples}}}"

        self._query(
            url=f"{self.connection_url}/update",
            method=POST,
            query=query,
        )

        print(g.serialize(format="turtle"))

    def load(self, id: str = None) -> Graph:
        if id:
            query = f"CONSTRUCT {{ ?s ?p ?o }} WHERE {{ GRAPH <{id}> {{ ?s ?p ?o }} }}"
        else:
            query = "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"

        response = self._query(
            url=f"{self.connection_url}/sparql",
            method=POST,
            query=query,
        )

        print(response)

        g = Graph()
        g.parse(data=response, format="turtle")

        print(g.serialize(format="turtle"))

        return g
