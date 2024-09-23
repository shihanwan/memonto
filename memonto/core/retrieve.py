from rdflib import Graph
from rdflib.namespace import RDF, RDFS, OWL

from memonto.llms.base_llm import LLMModel
from memonto.utils.rdf import is_rdf_schema


def fetch_memory(g: Graph, llm: LLMModel) -> str:
    filtered_g = Graph()

    for s, p, o in g:
        if is_rdf_schema(p):
            continue

        filtered_g.add((s, p, o))

    memory = filtered_g.serialize(format="turtle")

    summarized_memory = llm.prompt(
        prompt_name="summarize_memory",
        memory=memory,
    )

    return summarized_memory
