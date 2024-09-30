import pytest
from rdflib import Graph, Literal, URIRef
from unittest.mock import ANY, MagicMock, Mock, patch

from memonto.core.retrieve import _retrieve


@pytest.fixture
def data_graph():
    g = Graph()

    g.add(
        (
            URIRef("http://example.org/test#subject1"),
            URIRef("http://example.org/test#predicate1"),
            Literal("object1"),
        )
    )
    g.add(
        (
            URIRef("http://example.org/test#subject2"),
            URIRef("http://example.org/test#predicate2"),
            Literal("object2"),
        )
    )
    g.add(
        (
            URIRef("http://example.org/test#subject3"),
            URIRef("http://example.org/test#predicate3"),
            Literal("object3"),
        )
    )

    return g


def test_retrive_memory_ephemeral(data_graph):
    mem_data = _retrieve(
        ontology=Mock(),
        data=data_graph,
        triple_store=None,
        id=None,
        uri=URIRef("http://example.org/test#subject1"),
        query=None,
        ephemeral=True,
    )

    assert mem_data == [
        {
            "s": URIRef("http://example.org/test#subject1"),
            "p": URIRef("http://example.org/test#predicate1"),
            "o": Literal("object1"),
        }
    ]
