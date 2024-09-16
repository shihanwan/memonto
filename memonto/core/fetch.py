from rdflib import Graph
from rdflib.namespace import RDF, RDFS

from memonto.llms.base_llm import LLMModel
from memonto.stores.base_store import StoreModel


def fetch_memory(
    self,
    llm: LLMModel,
    store: StoreModel,
    id: str = None,
) -> str:
    g = store.load(id=id, debug=self.debug)
    self.g = g

    filters = {RDFS.domain, RDFS.range, RDFS.subClassOf, RDFS.subPropertyOf}
    filtered_g = Graph()

    for s, p, o in g:
        if p in filters or (p == RDF.type and o == RDFS.Class):
            continue
        filtered_g.add((s, p, o))

    memory = filtered_g.serialize(format="turtle")

    summarized_memory = llm.prompt(
        prompt_name="summarize_memory",
        memory=memory,
    )

    return summarized_memory
