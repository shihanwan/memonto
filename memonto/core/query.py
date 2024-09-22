from rdflib import Graph, URIRef

from memonto.stores.base_store import StoreModel


def query_memory_store(store: StoreModel, id: str, uri: URIRef, query: str) -> None:
    if query:
        return store.get_raw(query=query)
    else:
        return store.get(id=id, uri=uri)
