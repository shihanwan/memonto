from rdflib import Graph

from memonto.llms.base_llm import LLMModel
from memonto.utils.rdf import is_rdf_schema
from memonto.stores.triple.base_store import TripleStoreModel
from memonto.stores.vector.base_store import VectorStoreModel


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


def recall_memory(
    data: Graph,
    llm: LLMModel,
    vector_store: VectorStoreModel,
    triple_store: TripleStoreModel,
    message: str,
    id: str,
) -> str:
    if vector_store is None:
        raise Exception("Vector store is not configured.")

    matched_triples = vector_store.search(message=message, id=id)
    triples = _hydrate_triples(matched_triples, triple_store, id=id)
    contextual_memory = _find_adjacent_triples(triples, triple_store, id=id)

    summarized_memory = llm.prompt(
        prompt_name="summarize_memory",
        memory=contextual_memory,
    )

    return summarized_memory
