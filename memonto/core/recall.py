from rdflib import Graph, URIRef, Literal, BNode

from memonto.llms.base_llm import LLMModel
from memonto.stores.triple.base_store import TripleStoreModel
from memonto.stores.vector.base_store import VectorStoreModel
from memonto.utils.logger import logger


def _hydrate_triples(
    triples: list,
    triple_store: VectorStoreModel,
    id: str = None,
) -> Graph:
    triple_values = " ".join(
        f"(<{triple['s']}> <{triple['p']}> \"{triple['o']}\")" for triple in triples
    )

    graph_id = f"data-{id}" if id else "data"

    query = f"""
    CONSTRUCT {{
        ?s ?p ?o .
    }}
    WHERE {{
        GRAPH <{graph_id}> {{
            VALUES (?s ?p ?o) {{ {triple_values} }}
            ?s ?p ?o .
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

    return triple_store.query(query=query, format="turtle")


def _find_all(triple_store: TripleStoreModel) -> str:
    return triple_store.query(
        query="CONSTRUCT {?s ?p ?o .} WHERE { GRAPH ?g { ?s ?p ?o . }}",
        format="turtle",
    )


def _recall(
    data: Graph,
    llm: LLMModel,
    vector_store: VectorStoreModel,
    triple_store: TripleStoreModel,
    context: str,
    id: str,
    ephemeral: bool,
) -> str:
    if ephemeral:
        memory = data.serialize(format="turtle")
    elif context:
        try:
            matched_triples = vector_store.search(message=context, id=id)

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
            memory = ""
    else:
        memory = _find_all(triple_store=triple_store, id=id)

    logger.debug(f"Contextual Triples\n{memory}\n")

    summarized_memory = llm.prompt(
        prompt_name="summarize_memory",
        context=context,
        memory=memory,
    )

    logger.debug(f"Summarized Memory\n{summarized_memory}\n")

    return summarized_memory
