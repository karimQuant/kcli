import os
import shutil
from unittest.mock import patch

import numpy as np
import pytest

import kcli.main as main
from kcli import storage

TEST_DIR = ".test_kcli"


@pytest.fixture(autouse=True)
def override_paths(request) -> None:
    """Overrides the DB_PATH and INDEX_PATH to use a unique test directory for each test."""
    # Create a unique test directory for this test
    test_id = request.node.nodeid.replace("/", "_").replace(":", "_")
    test_dir = os.path.join(TEST_DIR, test_id)
    os.makedirs(test_dir, exist_ok=True)

    # Set environment variables for this test
    os.environ["KCLI_TEST_MODE"] = "True"
    os.environ["KCLI_DB_PATH"] = os.path.join(test_dir, "test.db")
    os.environ["KCLI_INDEX_PATH"] = os.path.join(test_dir, "test.index")

    # Configure storage with new paths
    storage.configure()
    main.storage = storage.Storage()
    yield

    # Cleanup after test
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)


@pytest.fixture(autouse=True)
def mock_litellm() -> None:
    """Mocks litellm to return an array of ones for embeddings."""
    with patch("litellm.embedding") as mock_embedding:
        mock_embedding.return_value = {"data": [{"embedding": np.ones(1500).tolist()}]}
        yield mock_embedding
