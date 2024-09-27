from rdflib import URIRef, Graph

from memonto.stores.triple.base_store import TripleStoreModel


def _retrieve(
    ontology: Graph,
    triple_store: TripleStoreModel,
    id: str,
    uri: URIRef,
    query: str,
) -> list:
    if query:
        return triple_store.query(query=query)
    else:
        return triple_store.get(ontology=ontology, uri=uri, id=id)
