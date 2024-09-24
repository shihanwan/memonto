import pytest
from rdflib import Graph, Namespace
from unittest.mock import ANY, MagicMock, call

from memonto.core.retain import retain_memory


@pytest.fixture
def graph():
    return Graph()


@pytest.fixture
def namespace():
    return Namespace("http://example.org/")


@pytest.fixture
def user_query():
    return "some user query about Napoleon"


@pytest.fixture
def id():
    return "test-id-123"


@pytest.fixture
def mock_llm():
    mock_llm = MagicMock()
    mock_llm.prompt = MagicMock(return_value="script")
    return mock_llm


@pytest.fixture
def mock_store():
    mock_store = MagicMock()
    return mock_store


def test_commit_memory(
    graph,
    namespace,
    mock_llm,
    mock_store,
    user_query,
    id,
):
    retain_memory(
        g=graph,
        n=namespace,
        llm=mock_llm,
        store=mock_store,
        query=user_query,
        id=id,
        auto_expand=False,
        debug=False,
    )

    commit_to_memory = call(
        prompt_name="commit_to_memory",
        temperature=0.2,
        ontology=ANY,
        user_message=user_query,
        instruction=ANY,
    )

    commit_to_memory_error_handling = call(
        prompt_name="commit_to_memory_error_handling",
        temperature=ANY,
        error=ANY,
        script=ANY,
        ontology=ANY,
        user_message=user_query,
    )

    assert mock_llm.prompt.call_count == 2
    assert mock_llm.prompt.call_args_list == [
        commit_to_memory,
        commit_to_memory_error_handling,
    ]
    mock_store.save.assert_called_once_with(graph, id)


def test_commit_memory_auto_expand(
    graph,
    namespace,
    mock_llm,
    mock_store,
    user_query,
    id,
):
    retain_memory(
        g=graph,
        n=namespace,
        llm=mock_llm,
        store=mock_store,
        query=user_query,
        id=id,
        auto_expand=True,
        debug=False,
    )

    commit_to_memory = call(
        prompt_name="commit_to_memory",
        temperature=0.5,
        ontology=ANY,
        user_message=user_query,
        instruction=ANY,
    )

    commit_to_memory_error_handling = call(
        prompt_name="commit_to_memory_error_handling",
        temperature=ANY,
        error=ANY,
        script=ANY,
        ontology=ANY,
        user_message=user_query,
    )

    assert mock_llm.prompt.call_count == 2
    assert mock_llm.prompt.call_args_list == [
        commit_to_memory,
        commit_to_memory_error_handling,
    ]
    mock_store.save.assert_called_once_with(graph, id)
