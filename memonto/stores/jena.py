from rdflib import Graph, Literal, URIRef
from SPARQLWrapper import SPARQLWrapper, GET, POST, TURTLE, JSON
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException

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
            response = sparql.query()
            content_type = response.info()["Content-Type"]

            if "html" in content_type:
                return response.response.read().decode("utf-8")
            else:
                return response.convert()
        except SPARQLWrapperException as e:
            print(f"SPARQL query error: {e}")
        except Exception as e:
            print(f"Generic error: {e}")

    def _get_prefixes(self, g: Graph):
        gt = g.serialize(format="turtle")
        return [line for line in gt.splitlines() if line.startswith("@prefix")]

    def save(self, g: Graph, id: str = None, debug: bool = False) -> None:
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

        if debug:
            print(g.serialize(format="turtle"))

    def load(self, id: str = None, debug: bool = False) -> Graph:
        if id:
            query = f"CONSTRUCT {{ ?s ?p ?o }} WHERE {{ GRAPH <{id}> {{ ?s ?p ?o }} }}"
        else:
            query = "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"

        response = self._query(
            url=f"{self.connection_url}/sparql",
            method=POST,
            query=query,
        )

        g = Graph()
        g.parse(data=response, format="turtle")

        if debug:
            print(g.serialize(format="turtle"))

        return g

    def get(self, id: str, uri: URIRef, debug: bool = False) -> list:
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>

        SELECT ?s ?p ?o WHERE {{
            GRAPH <{id}> {{
                ?s ?p ?o .
                FILTER (?s = <{str(uri)}> || ?p = <{str(uri)}> || ?o = <{str(uri)}> )
                FILTER (?p != rdfs:domain && ?p != rdfs:range && ?p != rdfs:subClassOf)
            }}
        }}
        """

        result = self._query(
            url=f"{self.connection_url}/sparql",
            method=GET,
            query=query,
            format=JSON,
        )

        return result["results"]["bindings"]

    def get_raw(self, query: str) -> list:
        result = self._query(
            url=f"{self.connection_url}/sparql",
            method=GET,
            query=query,
            format=JSON,
        )

        return result["results"]["bindings"]
