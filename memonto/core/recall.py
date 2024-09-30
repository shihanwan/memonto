import json
from rdflib import Graph

from memonto.llms.base_llm import LLMModel
from memonto.stores.triple.base_store import TripleStoreModel
from memonto.stores.vector.base_store import VectorStoreModel
from memonto.utils.logger import logger


def _hydrate_triples(
    triples: list,
    triple_store: VectorStoreModel,
    id: str = None,
) -> list:
    triple_values = " ".join(
        f"(<{triple['s']}> <{triple['p']}> \"{triple['o']}\")" for triple in triples
    )

    graph_id = f"data-{id}" if id else "data"

    query = f"""
    SELECT ?s ?p ?o
    WHERE {{
        GRAPH <{graph_id}> {{
            VALUES (?s ?p ?o) {{ {triple_values} }}
        }}
    }}
    """

    return triple_store.query(query=query)


def _find_adjacent_triples(
    triples: list,
    triple_store: VectorStoreModel,
    id: str = None,
) -> str:
    nodes_set = set()

    for t in triples:
        for key in ["s", "o"]:
            node = t[key]
            node_value = node["value"]
            node_type = node["type"]

            if node_type == "uri":
                formatted_node = f"<{node_value}>"
            elif node_type == "literal":
                formatted_node = f'"{node_value}"'
            else:
                formatted_node = f'"{node_value}"'

            nodes_set.add(formatted_node)

    node_list = ", ".join(nodes_set)
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
    message: str,
    id: str,
    ephemeral: bool,
) -> str:
    if ephemeral:
        contextual_memory = data.serialize(format="turtle")
    elif message:
        try:
            matched_triples = vector_store.search(message=message, id=id)
            triples = _hydrate_triples(
                triples=matched_triples,
                triple_store=triple_store,
                id=id,
            )
            contextual_memory = _find_adjacent_triples(
                triples=triples,
                triple_store=triple_store,
                id=id,
            )

            logger.debug(f"Matched Triples\n{json.dumps(triples, indent=2)}\n")
        except ValueError as e:
            logger.debug(f"Recall Exception\n{e}\n")
            contextual_memory = ""
    else:
        contextual_memory = _find_all(triple_store=triple_store, id=id)

    logger.debug(f"Contextual Triples\n{contextual_memory}\n")

    summarized_memory = llm.prompt(
        prompt_name="summarize_memory",
        memory=contextual_memory,
    )

    logger.debug(f"Summarized Memory\n{summarized_memory}\n")

    return summarized_memory
