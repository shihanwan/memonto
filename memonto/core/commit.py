from rdflib import Graph, Namespace

from memonto.llms.base_llm import LLMModel
from memonto.stores.base_store import StoreModel


def commit_memory(
    g: Graph,
    n: Namespace,
    llm: LLMModel,
    store: StoreModel,
    query: str,
    id: str = None,
    debug: bool = False,
) -> None:
    rdf_graph = g.serialize(format="turtle")

    script = llm.prompt(
        prompt_name="commit_to_memory",
        temperature=0.2,
        ontology=rdf_graph,
        user_message=query,
        instruction="- NEVER generate code that adds information that DOES NOT fit onto the ontology.",
    )

    if debug: print(script)

    # TODO: exception handling
    exec(script, {"g": g, "n": n})

    store.save(g, id)
