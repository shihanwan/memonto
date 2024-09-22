from rdflib import Graph

from memonto.stores.base_store import StoreModel


def load_memory(store: StoreModel, id: str, debug: bool) -> Graph:
    return store.load(id=id, debug=debug)
