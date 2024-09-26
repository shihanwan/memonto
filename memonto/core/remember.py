from rdflib import Graph, Namespace

from memonto.stores.triple.base_store import TripleStoreModel


def load_memory(
    namespaces: dict[str, Namespace],
    store: TripleStoreModel,
    id: str,
    debug: bool,
) -> Graph:
    return store.load(namespaces=namespaces, id=id, debug=debug)
