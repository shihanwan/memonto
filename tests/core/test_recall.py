import pytest
from rdflib import Graph, Literal, URIRef
from unittest.mock import ANY, MagicMock, patch

from memonto.core.recall import _recall


@pytest.fixture
def graph():
    return Graph()


@pytest.fixture
def user_query():
    return "some user query about Bismark"


@pytest.fixture
def id():
    return "test-id-123"


@pytest.fixture
def mock_llm():
    mock_llm = MagicMock()
    mock_llm.prompt = MagicMock(return_value="some summary")
    return mock_llm


@pytest.fixture
def mock_store():
    mock_store = MagicMock()
    return mock_store


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


@patch("memonto.core.recall._find_all")
def test_fetch_all_memory(mock_find_all, mock_llm, mock_store, id, data_graph):
    all_memory = "all memory"
    mock_find_all.return_value = all_memory

    _recall(
        data=data_graph,
        llm=mock_llm,
        vector_store=mock_store,
        triple_store=mock_store,
        message=None,
        id=id,
        ephemeral=False,
    )

    mock_llm.prompt.assert_called_once_with(
        prompt_name="summarize_memory",
        memory=all_memory,
    )


@patch("memonto.core.recall._find_adjacent_triples")
@patch("memonto.core.recall._hydrate_triples")
def test_fetch_some_memory(
    mock_hydrate_triples,
    mock_find_adjacent_triples,
    mock_llm,
    mock_store,
    user_query,
    id,
    data_graph,
):
    some_memory = "some memory"
    mock_find_adjacent_triples.return_value = some_memory
    mock_hydrate_triples.return_value = []

    _recall(
        data=data_graph,
        llm=mock_llm,
        vector_store=mock_store,
        triple_store=mock_store,
        message=user_query,
        id=id,
        ephemeral=False,
    )

    mock_llm.prompt.assert_called_once_with(
        prompt_name="summarize_memory",
        memory=some_memory,
    )


def test_fetch_some_memory_ephemeral(mock_llm, data_graph):

    mem = _recall(
        data=data_graph,
        llm=mock_llm,
        vector_store=None,
        triple_store=None,
        message=None,
        id=None,
        ephemeral=True,
    )

    assert mem == "some summary"
