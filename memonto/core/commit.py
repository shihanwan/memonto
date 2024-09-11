from rdflib import Graph, Namespace

from memonto.llms.base_llm import LLMModel

def commit_memory(g: Graph, EX: Namespace, llm: LLMModel, query: str) -> None:
    rdf_graph = g.serialize(format="turtle")

    new_memory = llm.prompt(
        prompt="commit_to_memory",
        temperature=0.2,
        ontology=rdf_graph,
        user_message=query,
    )

    exec(new_memory, {"g": g, "EX": EX})