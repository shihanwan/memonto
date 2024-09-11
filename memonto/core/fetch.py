from rdflib import Graph
from rdflib.namespace import RDF, RDFS

from memonto.llms.base_llm import LLMModel


def fetch_memory(g: Graph, llm: LLMModel) -> str:
    entity_graph = Graph()
    schema_predicates = {RDFS.domain, RDFS.range, RDFS.subClassOf, RDFS.subPropertyOf}

    for subj, pred, obj in g:
        if pred in schema_predicates or (pred == RDF.type and obj == RDFS.Class):
            continue

        entity_graph.add((subj, pred, obj))

    memory = entity_graph.serialize(format="turtle")

    summarize_memory = llm.prompt(
        prompt="summarize_memory",
        memory=memory,
    )

    return summarize_memory
