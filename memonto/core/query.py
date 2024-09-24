from rdflib import URIRef, Graph, Namespace

from memonto.stores.base_store import StoreModel


def query_memory_data(
    ontology: Graph,
    store: StoreModel,
    id: str,
    uri: URIRef,
    query: str,
    debug: bool,
) -> list:
    if query:
        return store.get_raw(query=query)
    else:
        return store.get(
            ontology=ontology,
            id=id,
            uri=uri,
            debug=debug,
        )
