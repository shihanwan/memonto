from rdflib import Graph
from rdflib.namespace import RDF, RDFS

from memonto.llms.base_llm import LLMModel
from memonto.stores.base_store import StoreModel    


def fetch_memory(g: Graph, llm: LLMModel, store: StoreModel, id: str = None) -> str:
    entity_graph = store.load(id=id)
    schema_predicates = {RDFS.domain, RDFS.range, RDFS.subClassOf, RDFS.subPropertyOf}

    for subj, pred, obj in g:
        if pred in schema_predicates or (pred == RDF.type and obj == RDFS.Class):
            continue

        entity_graph.add((subj, pred, obj))

    memory = entity_graph.serialize(format="turtle")

    summarize_memory = llm.prompt(
        prompt_name="summarize_memory",
        memory=memory,
    )

    return summarize_memory
