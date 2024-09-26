from rdflib import URIRef, Graph, Namespace

from memonto.stores.triple.base_store import TripleStoreModel


def query_memory_data(
    ontology: Graph,
    store: TripleStoreModel,
    id: str,
    uri: URIRef,
    query: str,
    debug: bool,
) -> list:
    if query:
        return store.query(query=query)
    else:
        return store.get(
            ontology=ontology,
            id=id,
            uri=uri,
            debug=debug,
        )
