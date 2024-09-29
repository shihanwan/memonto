import pytest
from pydantic import ValidationError

from memonto.core.configure import _configure
from memonto.llms.openai import OpenAI
from memonto.llms.anthropic import Anthropic
from memonto.stores.triple.jena import ApacheJena
from memonto.stores.vector.chroma import Chroma


@pytest.fixture
def anthropic_provider():
    return "anthropic"


@pytest.fixture
def anthropic_model():
    return "gpt-4o"


@pytest.fixture
def openai_provider():
    return "openai"


@pytest.fixture
def openai_model():
    return "gpt-4o"


@pytest.fixture
def api_key():
    return "test-sk-123"


@pytest.fixture
def triple_store_provider():
    return "apache_jena"


@pytest.fixture
def jena_url():
    return "http://localhost:8080/test-dataset"


@pytest.fixture
def vector_store_provider():
    return "chroma"


def test_configure_with_unsupported_provider(api_key):
    config = {
        "model": {
            "provider": "random_model_provider",
            "config": {
                "model": "random_model_name",
                "api_key": api_key,
            },
        }
    }

    with pytest.raises(ValueError):
        _configure(config)


def test_configure_with_openai_config(openai_provider, openai_model, api_key):
    config = {
        "model": {
            "provider": openai_provider,
            "config": {
                "model": openai_model,
                "api_key": api_key,
            },
        }
    }

    ts, vs, llm = _configure(config)

    assert isinstance(llm, OpenAI)
    assert ts is None
    assert vs is None


def test_configure_with_bad_openai_config(openai_provider, api_key):
    config = {
        "model": {
            "provider": openai_provider,
            "config": {
                "api_key": api_key,
            },
        }
    }

    with pytest.raises(ValidationError):
        _configure(config)


def test_configure_with_anthropic_config(anthropic_provider, anthropic_model, api_key):
    config = {
        "model": {
            "provider": anthropic_provider,
            "config": {
                "model": anthropic_model,
                "api_key": api_key,
            },
        }
    }

    ts, vs, llm = _configure(config)

    assert isinstance(llm, Anthropic)
    assert ts is None
    assert vs is None


def test_configure_with_bad_anthropic_config(anthropic_provider, anthropic_model):
    config = {
        "model": {
            "provider": anthropic_provider,
            "config": {
                "model": anthropic_model,
            },
        }
    }

    with pytest.raises(ValidationError):
        _configure(config)


def test_configure_with_apache_jena_config(triple_store_provider, jena_url):
    config = {
        "triple_store": {
            "provider": triple_store_provider,
            "config": {
                "connection_url": jena_url,
            },
        },
    }

    ts, vs, llm = _configure(config)

    assert isinstance(ts, ApacheJena)
    assert vs is None
    assert llm is None


def test_configure_with_bad_apache_jena_config(triple_store_provider, jena_url):
    config = {
        "triple_store": {
            "provider": triple_store_provider,
            "config": {
                "url": jena_url,
            },
        },
    }

    with pytest.raises(ValidationError):
        _configure(config)


def test_configure_with_chroma_config(vector_store_provider, jena_url):
    config = {
        "vector_store": {
            "provider": vector_store_provider,
            "config": {
                "model": "local",
                "path": ".local",
            },
        },
    }

    ts, vs, llm = _configure(config)

    assert isinstance(vs, Chroma)
    assert ts is None
    assert llm is None
