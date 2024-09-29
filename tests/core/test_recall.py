import pytest
from rdflib import Graph
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


@patch("memonto.core.recall._find_all")
def test_fetch_all_memory(mock_find_all, mock_llm, mock_store, id):
    all_memory = "all memory"
    mock_find_all.return_value = all_memory

    _recall(
        llm=mock_llm,
        vector_store=mock_store,
        triple_store=mock_store,
        message=None,
        id=id,
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
):
    some_memory = "some memory"
    mock_find_adjacent_triples.return_value = some_memory
    mock_hydrate_triples.return_value = []

    _recall(
        llm=mock_llm,
        vector_store=mock_store,
        triple_store=mock_store,
        message=user_query,
        id=id,
    )

    mock_llm.prompt.assert_called_once_with(
        prompt_name="summarize_memory",
        memory=some_memory,
    )
