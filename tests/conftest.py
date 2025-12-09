# -*- coding: utf-8 -*-

"""
Pytest configuration and fixtures for home_secret_toml tests.
"""

import typing as T
import pytest
import tomllib
from pathlib import Path

from home_secret_toml.paths import path_enum


# Path to test fixtures
dir_fixtures = path_enum.dir_unit_test / "fixtures"
path_test_toml = dir_fixtures / "home_secret.toml"


@pytest.fixture
def home_secret_data() -> dict[str, T.Any]:
    """
    Fixture that loads and returns the test TOML data as a nested dictionary.

    This fixture provides the parsed TOML data from the test fixture file,
    which can be used directly in tests that need access to the raw data
    structure without going through HomeSecretToml.
    """
    return tomllib.loads(path_test_toml.read_text(encoding="utf-8"))


@pytest.fixture
def home_secret_path() -> Path:
    """
    Fixture that returns the path to the test TOML fixture file.

    This fixture is used to create HomeSecretToml instances with
    a custom path pointing to the test fixture.
    """
    return path_test_toml
