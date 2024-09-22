from rdflib import Graph
from rdflib.namespace import RDF, RDFS

from memonto.llms.base_llm import LLMModel


def fetch_memory(g: Graph, llm: LLMModel) -> str:
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
