"""Pytest fixtures shared across test modules."""

import pytest
from core.tools import ToolRegistry
from core.memory import Memory


@pytest.fixture
def empty_tools():
    """A fresh, empty ToolRegistry."""
    return ToolRegistry()


@pytest.fixture
def memory():
    """A fresh Memory instance."""
    return Memory()
