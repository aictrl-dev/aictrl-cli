import pytest
from pathlib import Path


@pytest.fixture
def sample_project():
    return Path(__file__).parent / "fixtures" / "sample-project"


@pytest.fixture
def aictrl_dir(sample_project):
    return sample_project / ".aictrl"
