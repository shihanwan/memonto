from rdflib import Graph

from memonto.stores.base_store import StoreModel


def load_memory(store: StoreModel, id: str = None, debug: bool = False) -> Graph:
    return store.load(id=id, debug=debug)
