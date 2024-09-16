from rdflib import Graph, Namespace

from memonto.llms.base_llm import LLMModel
from memonto.stores.base_store import StoreModel


def commit_memory(
    self,
    g: Graph,
    n: Namespace,
    llm: LLMModel,
    store: StoreModel,
    query: str,
    id: str = None,
) -> None:
    rdf_graph = g.serialize(format="turtle")

    script = llm.prompt(
        prompt_name="commit_to_memory",
        temperature=0.2,
        ontology=rdf_graph,
        user_message=query,
    )

    # TODO: exception handling
    exec(script, {"g": g, "n": n})

    store.save(g, id)
