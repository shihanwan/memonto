import json
from rdflib import Graph, Literal, Namespace, URIRef
from SPARQLWrapper import SPARQLWrapper, GET, POST, TURTLE, JSON
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException
from typing import Tuple

from memonto.stores.triple.base_store import TripleStoreModel
from memonto.utils.logger import logger
from memonto.utils.namespaces import TRIPLE_PROP
from memonto.utils.rdf import format_node


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

    def _hydrate_triples(
        self,
        matched: list,
        graph_id: str = None,
    ) -> Graph:
        matched_ids = matched.keys()
        triple_ids = " ".join(f'("{id}")' for id in matched_ids)
        g_id = f"data-{graph_id}" if graph_id else "data"

        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

        CONSTRUCT {{
            ?s ?p ?o .
        }}
        WHERE {{
            GRAPH <{g_id}> {{
                VALUES (?uuid) {{ {triple_ids} }}
                ?triple_node <{TRIPLE_PROP.uuid}> ?uuid .
                ?triple_node rdf:subject ?s ;
                            rdf:predicate ?p ;
                            rdf:object ?o .
            }}
        }}
        """

        result = self._query(
            url=f"{self.connection_url}/sparql",
            method=GET,
            query=query,
        )

        g = Graph()
        g.parse(data=result, format="turtle")

        return g

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

    def get_all(self, graph_id: str = None) -> str:
        g_id = f"data-{graph_id}" if graph_id else "data"

        query = f"""
        CONSTRUCT {{
            ?s ?p ?o .
        }} WHERE {{
            GRAPH <{g_id}> {{
                ?s ?p ?o .
                FILTER NOT EXISTS {{ ?s <{TRIPLE_PROP.uuid}> ?uuid }}
            }}
        }}
        """

        result = self._query(
            url=f"{self.connection_url}/sparql",
            method=GET,
            query=query,
        )

        if isinstance(result, bytes):
            result = result.decode("utf-8")

        if not result:
            return ""

        return str(result)

    def get_context(
        self, matched: dict[str, dict], graph_id: str, depth: int = 1
    ) -> str:
        g_id = f"data-{graph_id}" if graph_id else "data"
        nodes_set = set()

        matched_graph = self._hydrate_triples(
            matched=matched,
            graph_id=graph_id,
        )
        logger.debug(f"Matched Triples\n{matched_graph.serialize(format='turtle')}\n")

        for s, p, o in matched_graph:
            nodes_set.add(format_node(s))
            nodes_set.add(format_node(o))

        explored_nodes = set(nodes_set)
        new_nodes_set = nodes_set.copy()

        query = None

        for _ in range(depth):
            if not new_nodes_set:
                break

            node_list = ", ".join(new_nodes_set)

            query = f"""
            CONSTRUCT {{
                ?s ?p ?o .
            }}
            WHERE {{
                GRAPH <{g_id}> {{
                    ?s ?p ?o .
                    FILTER (
                        (?s IN ({node_list}) || ?o IN ({node_list})) &&
                        NOT EXISTS {{ ?s <{TRIPLE_PROP.uuid}> ?uuid }}
                    )
                }}
            }}
            """

            logger.debug(f"Find adjacent triples SPARQL query\n{query}\n")

            try:
                result_triples = self.query(query=query, format="turtle")
            except Exception as e:
                raise ValueError(f"SPARQL Query Error: {e}")

            if result_triples is None:
                raise ValueError("SPARQL query returned no results")

            graph = Graph()
            graph.parse(data=result_triples, format="turtle")

            temp_new_nodes_set = set()
            for s, p, o in graph:
                formatted_subject = format_node(s)
                formatted_object = format_node(o)

                if formatted_subject not in explored_nodes:
                    temp_new_nodes_set.add(formatted_subject)
                    explored_nodes.add(formatted_subject)

                if formatted_object not in explored_nodes:
                    temp_new_nodes_set.add(formatted_object)
                    explored_nodes.add(formatted_object)

            new_nodes_set = temp_new_nodes_set

        if query is None:
            return ""

        result = self.query(query=query, format="turtle")
        logger.debug(f"Adjacent Triples\n{result}\n")

        return result

    def delete_all(self, graph_id: str = None) -> None:
        d_id = f"data-{graph_id}" if graph_id else "data"
        o_id = f"ontology-{graph_id}" if graph_id else "ontology"

        query = f"""DROP GRAPH <{o_id}> ; DROP GRAPH <{d_id}> ;"""

        self._query(
            url=f"{self.connection_url}/update",
            method=POST,
            query=query,
        )

    def delete_by_ids(self, ids: list[str], graph_id: str = None) -> None:
        g_id = f"data-{graph_id}" if graph_id else "data"
        t_ids = " ".join(f'"{id}"' for id in ids)

        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

        DELETE {{
            GRAPH <{g_id}> {{
                ?triple_node <{TRIPLE_PROP.uuid}> ?uuid .
                ?triple_node rdf:subject ?s ;
                            rdf:predicate ?p ;
                            rdf:object ?o .
                ?s ?p ?o .
            }}
        }}
        WHERE {{
            VALUES ?uuid {{ {t_ids} }}
            GRAPH <{g_id}> {{
                ?triple_node <{TRIPLE_PROP.uuid}> ?uuid .
                ?triple_node rdf:subject ?s ;
                            rdf:predicate ?p ;
                            rdf:object ?o .
                ?s ?p ?o .
            }}
        }}
        """

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
