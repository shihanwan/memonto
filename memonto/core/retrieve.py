from rdflib import URIRef, Graph

from memonto.stores.triple.base_store import TripleStoreModel


def get_triples_with_uri(g: Graph, uri: str) -> list[dict]:
    uri_ref = URIRef(uri)
    triples = []

    for s, p, o in g.triples((uri_ref, None, None)):
        triples.append({"s": s, "p": p, "o": o})

    for s, p, o in g.triples((None, uri_ref, None)):
        triples.append({"s": s, "p": p, "o": o})

    for s, p, o in g.triples((None, None, uri_ref)):
        triples.append({"s": s, "p": p, "o": o})

    return triples


def _retrieve(
    ontology: Graph,
    data: Graph,
    triple_store: TripleStoreModel,
    id: str,
    uri: URIRef,
    query: str,
    ephemeral: bool,
) -> list:
    if ephemeral:
        return get_triples_with_uri(g=data, uri=uri)
    elif query:
        return triple_store.query(query=query)
    else:
        return triple_store.get(ontology=ontology, uri=uri, id=id)
