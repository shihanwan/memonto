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
    expand_ontology: bool = True,
) -> None:
    rdf_graph = g.serialize(format="turtle")

    if expand_ontology:
        instruction = "- If there are information that is valuable but doesn't fit onto the ontology then add them as well."
    else:
        instruction = "- NEVER generate code that adds information that DOES NOT fit onto the ontology."

    script = llm.prompt(
        prompt_name="commit_to_memory",
        temperature=0.2,
        ontology=rdf_graph,
        user_message=query,
        instruction=instruction,
    )

    if debug:
        print(script)

    # TODO: exception handling
    exec(script, {"g": g, "n": n})

    store.save(g, id)
