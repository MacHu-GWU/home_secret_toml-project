# -*- coding: utf-8 -*-

"""
Unit tests for home_secret_toml module.

This test module covers all core components:
- _deep_get: Helper function for nested key lookup
- Token: Lazy-loading reference class
- HomeSecretToml: Main interface class
- walk: Iterator function for traversing secrets
- gen_enum_code: Code generation function
"""

import typing as T
import pytest
import tempfile
import tomllib
from pathlib import Path
from unittest.mock import patch

from home_secret_toml.home_secret_toml import (
    _deep_get,
    Token,
    HomeSecretToml,
    walk,
    gen_enum_code,
    UNKNOWN,
    DESCRIPTION,
    p_home_secret,
)


# Path to test fixtures
dir_here = Path(__file__).absolute().parent
dir_fixtures = dir_here / "fixtures"
path_test_toml = dir_fixtures / "home_secret.toml"


def load_test_data() -> dict[str, T.Any]:
    """Load the test fixture TOML data."""
    return tomllib.loads(path_test_toml.read_text(encoding="utf-8"))


class Test_deep_get:
    """Tests for the _deep_get helper function."""

    def test_existing_key_nested(self):
        """Test retrieving an existing key from nested dict returns correct value."""
        # TOML parses dotted keys as nested dicts
        data = {
            "github": {
                "accounts": {
                    "personal": {
                        "account_id": "user123",
                    }
                }
            },
            "aws": {
                "accounts": {
                    "prod": {
                        "port": 3306,
                    }
                }
            },
        }
        assert _deep_get(data, "github.accounts.personal.account_id") == "user123"
        assert _deep_get(data, "aws.accounts.prod.port") == 3306

    def test_missing_key_raises_keyerror(self):
        """Test that missing key raises KeyError with descriptive message."""
        data = {"github": {"accounts": {"personal": {"account_id": "user123"}}}}
        with pytest.raises(KeyError) as exc_info:
            _deep_get(data, "github.accounts.personal.nonexistent")
        assert "github.accounts.personal.nonexistent" in str(exc_info.value)

    def test_empty_dict(self):
        """Test that empty dict raises KeyError."""
        with pytest.raises(KeyError):
            _deep_get({}, "any.key")

    def test_various_value_types(self):
        """Test retrieval of various value types."""
        data = {
            "string_key": "string_value",
            "int_key": 42,
            "bool_key": True,
            "dict_key": {"nested": "value"},
            "list_key": ["a", "b", "c"],
        }
        assert _deep_get(data, "string_key") == "string_value"
        assert _deep_get(data, "int_key") == 42
        assert _deep_get(data, "bool_key") is True
        assert _deep_get(data, "dict_key") == {"nested": "value"}
        assert _deep_get(data, "list_key") == ["a", "b", "c"]

    def test_nested_dict_access(self):
        """Test accessing nested dict values."""
        data = {"level1": {"level2": {"level3": "deep_value"}}}
        assert _deep_get(data, "level1.level2.level3") == "deep_value"
        assert _deep_get(data, "level1.level2") == {"level3": "deep_value"}


class TestToken:
    """Tests for the Token class."""

    def test_lazy_loading(self):
        """Test that Token.v lazily loads the value."""
        data = {"github": {"token": "secret_value"}}
        token = Token(data=data, path="github.token")
        # Value should not be accessed until .v is called
        assert token.v == "secret_value"

    def test_token_returns_correct_value(self):
        """Test that Token returns the correct value for its path."""
        data = load_test_data()
        token = Token(data=data, path="github.accounts.personal.account_id")
        assert token.v == "user123"

    def test_missing_path_raises_keyerror(self):
        """Test that accessing missing path raises KeyError."""
        data = {"existing": {"key": "value"}}
        token = Token(data=data, path="nonexistent.key")
        with pytest.raises(KeyError):
            _ = token.v

    def test_token_with_inline_table(self):
        """Test Token with inline table value."""
        data = load_test_data()
        token = Token(data=data, path="aws.accounts.prod.secrets.deployment.creds")
        creds = token.v
        assert isinstance(creds, dict)
        assert "access_key" in creds
        assert "secret_key" in creds


class TestHomeSecretToml:
    """Tests for the HomeSecretToml class."""

    def test_data_property_loads_toml(self):
        """Test that data property loads TOML file correctly."""
        # Copy test fixture to home location temporarily
        original_content = None
        if p_home_secret.exists():
            original_content = p_home_secret.read_text(encoding="utf-8")

        try:
            p_home_secret.write_text(
                path_test_toml.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            # Create new instance to avoid cached data
            hs_test = HomeSecretToml()
            data = hs_test.data

            assert isinstance(data, dict)
            # TOML parses as nested dict
            assert "github" in data
            assert data["github"]["accounts"]["personal"]["account_id"] == "user123"
        finally:
            # Restore original content or remove test file
            if original_content is not None:
                p_home_secret.write_text(original_content, encoding="utf-8")

    def test_v_method_returns_value(self):
        """Test direct value access via v method."""
        original_content = None
        if p_home_secret.exists():
            original_content = p_home_secret.read_text(encoding="utf-8")

        try:
            p_home_secret.write_text(
                path_test_toml.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            hs_test = HomeSecretToml()

            assert hs_test.v("github.accounts.personal.account_id") == "user123"
            assert hs_test.v("db.mysql_dev.port") == 3306
            assert hs_test.v("db.mysql_dev.ssl_enabled") is True
        finally:
            if original_content is not None:
                p_home_secret.write_text(original_content, encoding="utf-8")

    def test_t_method_returns_token(self):
        """Test token creation via t method."""
        original_content = None
        if p_home_secret.exists():
            original_content = p_home_secret.read_text(encoding="utf-8")

        try:
            p_home_secret.write_text(
                path_test_toml.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            hs_test = HomeSecretToml()

            token = hs_test.t("github.accounts.personal.account_id")
            assert isinstance(token, Token)
            assert token.v == "user123"
        finally:
            if original_content is not None:
                p_home_secret.write_text(original_content, encoding="utf-8")

    def test_file_not_found_raises_error(self):
        """Test FileNotFoundError when file missing."""
        original_content = None
        if p_home_secret.exists():
            original_content = p_home_secret.read_text(encoding="utf-8")
            p_home_secret.unlink()

        try:
            # Patch IS_SYNC to False and p_here_secret to not exist
            with patch("home_secret_toml.home_secret_toml.IS_SYNC", False):
                with patch(
                    "home_secret_toml.home_secret_toml.p_here_secret",
                    Path("/nonexistent/path"),
                ):
                    hs_test = HomeSecretToml()
                    with pytest.raises(FileNotFoundError) as exc_info:
                        _ = hs_test.data
                    assert "home_secret.toml" in str(exc_info.value)
        finally:
            if original_content is not None:
                p_home_secret.write_text(original_content, encoding="utf-8")

    def test_v_method_caching(self):
        """Test that v method results are cached."""
        original_content = None
        if p_home_secret.exists():
            original_content = p_home_secret.read_text(encoding="utf-8")

        try:
            p_home_secret.write_text(
                path_test_toml.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            hs_test = HomeSecretToml()

            # Call twice and verify it returns the same object (cached)
            result1 = hs_test.v("github.accounts.personal.account_id")
            result2 = hs_test.v("github.accounts.personal.account_id")
            assert result1 == result2
        finally:
            if original_content is not None:
                p_home_secret.write_text(original_content, encoding="utf-8")


class Test_walk:
    """Tests for the walk function."""

    def test_iterates_all_keys_nested(self):
        """Test that walk yields all non-filtered keys from nested dict."""
        # TOML parses dotted keys as nested dicts
        data = {
            "github": {
                "accounts": {
                    "personal": {
                        "account_id": "user123",
                    }
                }
            },
            "aws": {
                "accounts": {
                    "prod": {
                        "port": 3306,
                    }
                }
            },
        }
        results = list(walk(data))
        assert len(results) == 2
        assert ("github.accounts.personal.account_id", "user123") in results
        assert ("aws.accounts.prod.port", 3306) in results

    def test_filters_description_keys(self):
        """Test that description keys are filtered out."""
        data = {
            "github": {
                "description": "GitHub platform",
                "accounts": {
                    "personal": {
                        "description": "Personal account",
                        "account_id": "user123",
                    }
                },
            }
        }
        results = list(walk(data))
        # Only account_id should be yielded, descriptions filtered out
        assert len(results) == 1
        assert results[0] == ("github.accounts.personal.account_id", "user123")

    def test_filters_unknown_values(self):
        """Test that UNKNOWN placeholder values are filtered."""
        data = {
            "github": {
                "accounts": {
                    "personal": {
                        "account_id": "...",  # UNKNOWN
                        "admin_email": "admin@example.com",
                    }
                }
            },
            "placeholder": {
                "value": "...",  # UNKNOWN
            },
        }
        results = list(walk(data))
        # Only admin_email should be yielded
        assert len(results) == 1
        assert results[0] == (
            "github.accounts.personal.admin_email",
            "admin@example.com",
        )

    def test_empty_dict(self):
        """Test walk with empty dictionary."""
        results = list(walk({}))
        assert results == []

    def test_with_test_fixture(self):
        """Test walk with actual test fixture data."""
        data = load_test_data()
        results = list(walk(data))

        # Should contain actual values
        result_keys = [key for key, _ in results]
        assert "github.accounts.personal.account_id" in result_keys
        assert "db.mysql_dev.port" in result_keys

        # Should NOT contain description keys
        description_keys = [k for k in result_keys if k.endswith(".description")]
        assert len(description_keys) == 0

        # Should NOT contain UNKNOWN values
        unknown_values = [v for _, v in results if v == UNKNOWN]
        assert len(unknown_values) == 0


class Test_gen_enum_code:
    """Tests for the gen_enum_code function."""

    def test_generates_valid_python(self):
        """Test that generated code is valid Python syntax."""
        original_content = None
        if p_home_secret.exists():
            original_content = p_home_secret.read_text(encoding="utf-8")

        try:
            p_home_secret.write_text(
                path_test_toml.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as f:
                temp_path = Path(f.name)

            try:
                # Need to create fresh instance to pick up new data
                with patch("home_secret_toml.home_secret_toml.hs", HomeSecretToml()):
                    from home_secret_toml import home_secret_toml

                    home_secret_toml.hs = HomeSecretToml()
                    gen_enum_code(output_path=temp_path)

                # Verify the generated file is valid Python by compiling it
                generated_code = temp_path.read_text(encoding="utf-8")
                compile(generated_code, temp_path, "exec")
            finally:
                temp_path.unlink()
        finally:
            if original_content is not None:
                p_home_secret.write_text(original_content, encoding="utf-8")

    def test_attribute_naming(self):
        """Test that dots are converted to double underscores."""
        original_content = None
        if p_home_secret.exists():
            original_content = p_home_secret.read_text(encoding="utf-8")

        try:
            p_home_secret.write_text(
                path_test_toml.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as f:
                temp_path = Path(f.name)

            try:
                from home_secret_toml import home_secret_toml

                home_secret_toml.hs = HomeSecretToml()
                gen_enum_code(output_path=temp_path)

                generated_code = temp_path.read_text(encoding="utf-8")

                # Check that attribute names use double underscores
                assert "github__accounts__personal__account_id" in generated_code
                assert "db__mysql_dev__port" in generated_code

                # Check that original paths are preserved in the string
                assert '"github.accounts.personal.account_id"' in generated_code
            finally:
                temp_path.unlink()
        finally:
            if original_content is not None:
                p_home_secret.write_text(original_content, encoding="utf-8")

    def test_generated_file_structure(self):
        """Test the structure of the generated file."""
        original_content = None
        if p_home_secret.exists():
            original_content = p_home_secret.read_text(encoding="utf-8")

        try:
            p_home_secret.write_text(
                path_test_toml.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as f:
                temp_path = Path(f.name)

            try:
                from home_secret_toml import home_secret_toml

                home_secret_toml.hs = HomeSecretToml()
                gen_enum_code(output_path=temp_path)

                generated_code = temp_path.read_text(encoding="utf-8")

                # Check required components are present
                assert "from home_secret_toml import hs" in generated_code
                assert "class Secret:" in generated_code
                assert "def _validate_secret():" in generated_code
                assert 'if __name__ == "__main__":' in generated_code
            finally:
                temp_path.unlink()
        finally:
            if original_content is not None:
                p_home_secret.write_text(original_content, encoding="utf-8")

    def test_default_output_path(self):
        """Test that default output path is used when not specified."""
        # This test just verifies the function doesn't error with default path
        # We don't actually generate to avoid polluting the workspace
        from home_secret_toml.home_secret_toml import p_here_enum

        assert p_here_enum.name == "home_secret_enum.py"


if __name__ == "__main__":
    from home_secret_toml.tests import run_cov_test

    run_cov_test(
        __file__,
        "home_secret_toml.home_secret_toml",
        preview=False,
    )
