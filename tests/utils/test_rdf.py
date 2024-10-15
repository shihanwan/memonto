import pytest
from rdflib import Graph, URIRef, Literal, BNode

from memonto.utils.namespaces import TRIPLE_PROP
from memonto.utils.rdf import (
    find_updated_triples_ephemeral,
    hydrate_graph_with_ids,
    serialize_graph_without_ids,
)


@pytest.fixture
def graph():
    g = Graph()

    g.add(
        (
            URIRef("http://example.org/s1"),
            URIRef("http://example.org/p1"),
            URIRef("http://example.org/o1"),
        )
    )
    g.add(
        (
            URIRef("http://example.org/s2"),
            URIRef("http://example.org/p2"),
            URIRef("http://example.org/o2"),
        )
    )

    return g


@pytest.fixture
def bnode_graph():
    g = Graph()

    g.add(
        (
            URIRef("http://example.org/s"),
            URIRef("http://example.org/p"),
            URIRef("http://example.org/o"),
        )
    )
    g.add((BNode(), TRIPLE_PROP.uuid, Literal("12345")))

    return g


def test_serialize_graph(bnode_graph):
    g = serialize_graph_without_ids(bnode_graph)

    assert "12345" not in g
    assert "s" in g


def test_hydrate_graph_with_ids(graph):
    g = hydrate_graph_with_ids(graph)

    uuid_triples = [t for t in g if t[1] == TRIPLE_PROP.uuid]
    assert len(uuid_triples) == 2
    assert all(isinstance(t[2], Literal) for t in uuid_triples)


def test_find_updated_triples_ephemeral():
    original = [
        {"s": "1", "p": "2", "o": "3"},
        {"s": "3", "p": "2", "o": "1"},
        {"s": "5", "p": "7", "o": "9"},
    ]
    updated = [
        {"s": "1", "p": "2", "o": "9"},
        {"s": "9", "p": "2", "o": "1"},
        {"s": "5", "p": "7", "o": "9"},
    ]
    
    assert find_updated_triples_ephemeral(original, updated) == [
        {"s": "1", "p": "2", "o": "9"},
        {"s": "9", "p": "2", "o": "1"},
    ]


def test_find_updated_triples_ephemeral_no_updates():
    original = [
        {"s": "1", "p": "2", "o": "3"},
        {"s": "3", "p": "2", "o": "1"},
        {"s": "5", "p": "7", "o": "9"},
    ]
    updated = [
        {"s": "1", "p": "2", "o": "3"},
        {"s": "3", "p": "2", "o": "1"},
        {"s": "5", "p": "7", "o": "9"},
    ]
    
    assert find_updated_triples_ephemeral(original, updated) == []