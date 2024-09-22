import pytest
from pydantic import ValidationError
from unittest.mock import MagicMock

from memonto.core.configure import configure
from memonto.llms.openai import OpenAI
from memonto.llms.anthropic import Anthropic
from memonto.stores.jena import ApacheJena


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
def store_provider():
    return "apache_jena"


@pytest.fixture
def jena_url():
    return "http://localhost:8080/test-dataset"


@pytest.fixture
def mock_memonto():
    class MockMemonto:
        def __init__(self):
            self.store = None
            self.llm = None

    return MagicMock(spec=MockMemonto)


def test_configure_with_unsupported_provider(mock_memonto, api_key):
    config = {
        "model": {
            "provider": "random_model_provider",
            "config": {
                "model": "randome_model_name",
                "api_key": api_key,
            },
        }
    }

    with pytest.raises(ValueError):
        configure(self=mock_memonto, config=config)


def test_configure_with_openai_config(
    mock_memonto,
    openai_provider,
    openai_model,
    api_key,
):
    config = {
        "model": {
            "provider": openai_provider,
            "config": {
                "model": openai_model,
                "api_key": api_key,
            },
        }
    }

    configure(self=mock_memonto, config=config)

    assert isinstance(mock_memonto.llm, OpenAI)
    assert mock_memonto.llm.model == openai_model
    assert mock_memonto.llm.api_key == api_key


def test_configure_with_bad_openai_config(
    mock_memonto,
    openai_provider,
    openai_model,
    api_key,
):

    config = {
        "model": {
            "provider": openai_provider,
            "model": openai_model,
            "config": {
                "api_key": api_key,
            },
        }
    }

    with pytest.raises(ValidationError):
        configure(self=mock_memonto, config=config)


def test_configure_with_anthropic_config(
    mock_memonto,
    anthropic_provider,
    anthropic_model,
    api_key,
):
    config = {
        "model": {
            "provider": anthropic_provider,
            "config": {
                "model": anthropic_model,
                "api_key": api_key,
            },
        }
    }

    configure(self=mock_memonto, config=config)

    assert isinstance(mock_memonto.llm, Anthropic)
    assert mock_memonto.llm.model == anthropic_model
    assert mock_memonto.llm.api_key == api_key


def test_configure_with_bad_anthropic_config(
    mock_memonto,
    anthropic_provider,
    anthropic_model,
):
    config = {
        "model": {
            "provider": anthropic_provider,
            "config": {
                "model": anthropic_model,
            },
        }
    }

    with pytest.raises(ValidationError):
        configure(self=mock_memonto, config=config)


def test_configure_with_apache_jena_config(
    mock_memonto,
    store_provider,
    jena_url,
):
    config = {
        "store": {
            "provider": store_provider,
            "config": {
                "connection_url": jena_url,
            },
        },
    }

    configure(self=mock_memonto, config=config)

    assert isinstance(mock_memonto.store, ApacheJena)
    assert mock_memonto.store.name == store_provider
    assert mock_memonto.store.connection_url == jena_url


def test_configure_with_bad_apache_jena_config(
    mock_memonto,
    store_provider,
    jena_url,
):
    config = {
        "store": {
            "provider": store_provider,
            "config": {
                "url": jena_url,
            },
        },
    }

    with pytest.raises(ValidationError):
        configure(self=mock_memonto, config=config)
