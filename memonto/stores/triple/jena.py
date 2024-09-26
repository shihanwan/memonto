from rdflib import Graph, Literal, Namespace, URIRef
from SPARQLWrapper import SPARQLWrapper, GET, POST, TURTLE, JSON
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException
from typing import Tuple

from memonto.stores.triple.base_store import TripleStoreModel
from memonto.utils.logger import logger


class ApacheJena(TripleStoreModel):
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

        logger.debug(f"SPARQL Query\n{query}\n")

        try:
            response = sparql.query()
            content_type = response.info()["Content-Type"]

            if "html" in content_type:
                res = response.response.read().decode("utf-8")
                logger.debug(f"SPARQL Query Result\n{res}\n")
                return res
            else:
                res = response.convert()
                logger.debug(f"SPARQL Query Result\n{res}\n")
                return res
        except SPARQLWrapperException as e:
            logger.error(f"SPARQL Query Error\n{e}\n")
        except Exception as e:
            logger.error(f"Generic Query Error\n{e}\n")

    def _get_prefixes(self, g: Graph) -> list[str]:
        gt = g.serialize(format="turtle")
        return [line for line in gt.splitlines() if line.startswith("@prefix")]

    def _load(
        self,
        g: Graph,
        namespaces: dict[str, Namespace],
        id: str,
    ) -> Graph:
        query = f"CONSTRUCT {{ ?s ?p ?o }} WHERE {{ GRAPH <{id}> {{ ?s ?p ?o }} }}"

        response = self._query(
            url=f"{self.connection_url}/sparql",
            method=POST,
            query=query,
        )

        g.parse(data=response, format="turtle")

        for p, n in namespaces.items():
            g.bind(p, n)

        return g

    def save(
        self,
        ontology: Graph,
        data: Graph,
        id: str = None,
    ) -> None:
        o_triples = ontology.serialize(format="nt")
        d_triples = data.serialize(format="nt")
        prefixes = self._get_prefixes(ontology)
        prefix_block = (
            "\n".join(prefixes).replace("@prefix", "PREFIX").replace(" .", "")
        )

        if id:
            query = f"""{prefix_block} 
            INSERT DATA {{ 
                GRAPH <ontology-{id}> {{{o_triples}}} 
                GRAPH <data-{id}> {{{d_triples}}} 
            }}"""
        else:
            query = f"""{prefix_block} 
            INSERT DATA {{ 
                GRAPH <ontology> {{{o_triples}}} 
                GRAPH <data> {{{d_triples}}} 
            }}"""

        self._query(
            url=f"{self.connection_url}/update",
            method=POST,
            query=query,
        )

    def load(
        self,
        namespaces: dict[str, Namespace],
        id: str = None,
    ) -> Tuple[Graph, Graph]:
        ontology_id = f"ontology-{id}" if id else "ontology"
        data_id = f"data-{id}" if id else "data"

        ontology = Graph()
        data = Graph()

        ontology = self._load(
            g=ontology,
            namespaces=namespaces,
            id=ontology_id,
        )
        data = self._load(
            g=data,
            namespaces=namespaces,
            id=data_id,
        )

        logger.debug(f"Loaded Ontology Graph\n{ontology.serialize(format='turtle')}\n")
        logger.debug(f"Loaded Data Graph\n{data.serialize(format='turtle')}\n")

        return ontology, data

    def get(
        self,
        ontology: Graph,
        id: str,
        uri: URIRef,
    ) -> list:
        prefixes = self._get_prefixes(ontology)
        prefix_block = (
            "\n".join(prefixes).replace("@prefix", "PREFIX").replace(" .", "")
        )

        query = f"""{prefix_block}
        SELECT ?s ?p ?o WHERE {{
            GRAPH <data-{id}> {{
                ?s ?p ?o .
                FILTER (?o = <{str(uri)}> || ?s = <{str(uri)}> || ?p = <{str(uri)}>)
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

    def delete(self, id: str = None) -> None:
        query = f"""DROP GRAPH <ontology-{id}> ; DROP GRAPH <data-{id}> ;"""

        self._query(
            url=f"{self.connection_url}/update",
            method=POST,
            query=query,
        )

    def query(self, query: str, method: str = GET, format: str = JSON) -> list:
        result = self._query(
            url=f"{self.connection_url}/sparql",
            method=method,
            query=query,
            format=format,
        )

        if format == JSON:
            return result["results"]["bindings"]
        else:
            return result.decode("utf-8")
