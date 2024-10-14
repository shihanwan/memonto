from rdflib import Graph, URIRef, Literal, BNode

from memonto.llms.base_llm import LLMModel
from memonto.stores.triple.base_store import TripleStoreModel
from memonto.stores.vector.base_store import VectorStoreModel
from memonto.utils.logger import logger
from memonto.utils.namespaces import TRIPLE_PROP
from memonto.utils.rdf import serialize_graph_without_ids


def _hydrate_triples(
    triples: list,
    triple_store: VectorStoreModel,
    id: str = None,
) -> Graph:
    triple_ids = " ".join(f"(\"{triple_id}\")" for triple_id in triples)

    graph_id = f"data-{id}" if id else "data"

    query = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    CONSTRUCT {{
        ?s ?p ?o .
    }}
    WHERE {{
        GRAPH <{graph_id}> {{
            VALUES (?uuid) {{ {triple_ids} }}
            ?triple_node <{TRIPLE_PROP.uuid}> ?uuid .
            ?triple_node rdf:subject ?s ;
                         rdf:predicate ?p ;
                         rdf:object ?o .
        }}
    }}
    """

    result = triple_store.query(query=query, format="turtle")

    g = Graph()
    g.parse(data=result, format="turtle")

    return g


def _get_formatted_node(node: URIRef | Literal | BNode) -> str:
    if isinstance(node, URIRef):
        return f"<{str(node)}>"
    elif isinstance(node, Literal):
        return f'"{str(node)}"'
    elif isinstance(node, BNode):
        return f"_:{str(node)}"
    else:
        return f'"{str(node)}"'


def _find_adjacent_triples(
    triples: Graph,
    triple_store: VectorStoreModel,
    id: str = None,
    depth: int = 1,
) -> str:
    nodes_set = set()

    for s, p, o in triples:
        nodes_set.add(_get_formatted_node(s))
        nodes_set.add(_get_formatted_node(o))

    explored_nodes = set(nodes_set)
    new_nodes_set = nodes_set.copy()

    query = None

    for _ in range(depth):
        if not new_nodes_set:
            break

        node_list = ", ".join(new_nodes_set)
        graph_id = f"data-{id}" if id else "data"

        query = f"""
        CONSTRUCT {{
            ?s ?p ?o .
        }}
        WHERE {{
            GRAPH <{graph_id}> {{
                ?s ?p ?o .
                FILTER (?s IN ({node_list}) || ?o IN ({node_list}))
            }}
        }}
        """

        logger.debug(f"Find adjacent triples SPARQL query\n{query}\n")

        try:
            result_triples = triple_store.query(query=query, format="turtle")
        except Exception as e:
            raise ValueError(f"SPARQL Query Error: {e}")

        if result_triples is None:
            raise ValueError("SPARQL query returned no results")

        graph = Graph()
        graph.parse(data=result_triples, format="turtle")

        temp_new_nodes_set = set()
        for s, p, o in graph:
            formatted_subject = _get_formatted_node(s)
            formatted_object = _get_formatted_node(o)

            if formatted_subject not in explored_nodes:
                temp_new_nodes_set.add(formatted_subject)
                explored_nodes.add(formatted_subject)

            if formatted_object not in explored_nodes:
                temp_new_nodes_set.add(formatted_object)
                explored_nodes.add(formatted_object)

        new_nodes_set = temp_new_nodes_set

    if query is None:
        return ""

    return triple_store.query(query=query, format="turtle")


def _find_all(triple_store: TripleStoreModel, id: str) -> str:
    result = triple_store.query(
        query=f"""
        CONSTRUCT {{
            ?s ?p ?o .
        }} WHERE {{
            GRAPH <data-{id}> {{
                ?s ?p ?o .
                FILTER NOT EXISTS {{ ?s <{TRIPLE_PROP.uuid}> ?uuid }}
            }}
        }}
        """,
        format="turtle",
    )

    if isinstance(result, bytes):
        result = result.decode("utf-8")

    if not result:
        return ""

    return str(result)


def get_contextual_memory(
    data: Graph,
    vector_store: VectorStoreModel,
    triple_store: TripleStoreModel,
    context: str,
    id: str,
    ephemeral: bool,
):
    memory = ""

    if ephemeral:
        memory = serialize_graph_without_ids(data)
    elif context:
        try:
            matched_triples = vector_store.search(message=context, id=id)
            logger.debug(f"Matched Triples Raw\n{matched_triples}\n")

            matched_graph = _hydrate_triples(
                triples=matched_triples,
                triple_store=triple_store,
                id=id,
            )
            matched_triples = matched_graph.serialize(format="turtle")
            logger.debug(f"Matched Triples\n{matched_triples}\n")

            memory = _find_adjacent_triples(
                triples=matched_graph,
                triple_store=triple_store,
                id=id,
                depth=1,
            )
            logger.debug(f"Adjacent Triples\n{memory}\n")
        except ValueError as e:
            logger.debug(f"Recall Exception\n{e}\n")
    else:
        memory = _find_all(triple_store=triple_store, id=id)

    logger.debug(f"Contextual Memory\n{memory}\n")
    return memory


def _recall(
    data: Graph,
    llm: LLMModel,
    vector_store: VectorStoreModel,
    triple_store: TripleStoreModel,
    context: str,
    id: str,
    ephemeral: bool,
) -> str:
    memory = get_contextual_memory(
        data=data,
        vector_store=vector_store,
        triple_store=triple_store,
        context=context,
        id=id,
        ephemeral=ephemeral,
    )

    summarized_memory = llm.prompt(
        prompt_name="summarize_memory",
        context=context or "",
        memory=memory,
    )

    logger.debug(f"Summarized Memory\n{summarized_memory}\n")

    return summarized_memory
