import pytest
from rdflib import Graph, Namespace
from unittest.mock import ANY, MagicMock, call

from memonto.core.retain import _retain


@pytest.fixture
def graph():
    return Graph()


@pytest.fixture
def namespace():
    return {"ns": Namespace("http://example.org/")}


@pytest.fixture
def user_query():
    return "some user query about Napoleon"


@pytest.fixture
def id():
    return "test-id-123"


@pytest.fixture
def mock_llm():
    mock_llm = MagicMock()
    mock_llm.prompt = MagicMock(return_value="print('test')")
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
    _retain(
        ontology=graph,
        namespaces=namespace,
        data=graph,
        llm=mock_llm,
        triple_store=mock_store,
        vector_store=mock_store,
        message=user_query,
        id=id,
        auto_expand=False,
        auto_update=False,
        ephemeral=False,
    )

    ctm_prompt = call(
        prompt_name="commit_to_memory",
        temperature=0.2,
        ontology=ANY,
        user_message=user_query,
        updated_memory="",
        relevant_memory=ANY,
    )

    assert mock_llm.prompt.call_count == 1
    assert mock_llm.prompt.call_args_list == [ctm_prompt]


def test_commit_memory_with_exception(
    graph,
    namespace,
    mock_llm,
    mock_store,
    user_query,
    id,
):
    bad_script = "abcdef"
    mock_llm.prompt = MagicMock(return_value=bad_script)

    _retain(
        ontology=graph,
        namespaces=namespace,
        data=graph,
        llm=mock_llm,
        triple_store=mock_store,
        vector_store=mock_store,
        message=user_query,
        id=id,
        auto_expand=False,
        auto_update=False,
        ephemeral=False,
    )

    ctm_prompt = call(
        prompt_name="commit_to_memory",
        temperature=0.2,
        ontology=ANY,
        user_message=user_query,
        updated_memory="",
        relevant_memory=ANY,
    )

    ctmeh_prompt = call(
        prompt_name="commit_to_memory_error_handling",
        temperature=0.2,
        error=ANY,
        ontology=ANY,
        script=bad_script,
        user_message=user_query,
    )

    assert mock_llm.prompt.call_count == 2
    assert mock_llm.prompt.call_args_list == [ctm_prompt, ctmeh_prompt]


def test_commit_memory_auto_expand(
    graph,
    namespace,
    mock_llm,
    mock_store,
    user_query,
    id,
):
    _retain(
        ontology=graph,
        namespaces=namespace,
        data=graph,
        llm=mock_llm,
        triple_store=mock_store,
        vector_store=mock_store,
        message=user_query,
        id=id,
        auto_expand=True,
        auto_update=False,
        ephemeral=False,
    )

    ctm_prompt = call(
        prompt_name="commit_to_memory",
        temperature=0.2,
        ontology=ANY,
        user_message=user_query,
        updated_memory="",
        relevant_memory=ANY,
    )

    eo_prompt = call(
        prompt_name="expand_ontology",
        temperature=0.3,
        ontology=ANY,
        user_message=user_query,
    )

    assert mock_llm.prompt.call_count == 2
    assert mock_llm.prompt.call_args_list == [eo_prompt, ctm_prompt]
