from rdflib import Graph, Namespace

from memonto.stores.base_store import StoreModel


def load_memory(
    namespaces: dict[str, Namespace],
    store: StoreModel,
    id: str,
    debug: bool,
) -> Graph:
    return store.load(namespaces=namespaces, id=id, debug=debug)
