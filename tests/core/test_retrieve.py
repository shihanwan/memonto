import pytest
from rdflib import Graph
from unittest.mock import ANY, MagicMock

from memonto.core.retrieve import retrieve_memory


@pytest.fixture
def graph():
    return Graph()


@pytest.fixture
def mock_llm():
    mock_llm = MagicMock()
    mock_llm.prompt = MagicMock(return_value="some summary")
    return mock_llm


def test_fetch_memory(graph, mock_llm):
    res = retrieve_memory(data=graph, llm=mock_llm)

    mock_llm.prompt.assert_called_once_with(
        prompt_name="summarize_memory",
        memory=ANY,
    )

    assert res == "some summary"
