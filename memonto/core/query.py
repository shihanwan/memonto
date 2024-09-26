from rdflib import URIRef, Graph

from memonto.stores.triple.base_store import TripleStoreModel
from memonto.utils.decorators import require_config


@require_config("triple_store")
def query_memory_data(
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
