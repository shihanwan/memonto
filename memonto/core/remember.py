from rdflib import Graph, Namespace

from memonto.stores.triple.base_store import TripleStoreModel


def load_memory(
    namespaces: dict[str, Namespace],
    triple_store: TripleStoreModel,
    id: str,
) -> Graph:
    return triple_store.load(namespaces=namespaces, id=id)
