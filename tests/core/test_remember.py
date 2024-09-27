import pytest
from unittest.mock import MagicMock

from memonto.core.remember import _remember


@pytest.fixture
def id():
    return "test-id-123"


@pytest.fixture
def mock_store():
    mock_store = MagicMock()
    return mock_store


def test_load_memory(mock_store, id):
    _remember(
        triple_store=mock_store,
        id=id,
        debug=False,
    )

    mock_store.load.assert_called_once_with(id=id, debug=False)
