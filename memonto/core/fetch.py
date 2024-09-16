from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS

from memonto.llms.base_llm import LLMModel
from memonto.stores.base_store import StoreModel


def fetch_memory(
    self,
    llm: LLMModel,
    store: StoreModel,
    id: str = None,
) -> str:
    g = store.load(id=id)
    self.g = g

    schema_predicates = {RDFS.domain, RDFS.range, RDFS.subClassOf, RDFS.subPropertyOf}

    for subj, pred, obj in g:
        if pred in schema_predicates or (pred == RDF.type and obj == RDFS.Class):
            continue
        g.add((subj, pred, obj))

    memory = g.serialize(format="turtle")

    summarized_memory = llm.prompt(
        prompt_name="summarize_memory",
        memory=memory,
    )

    return summarized_memory
