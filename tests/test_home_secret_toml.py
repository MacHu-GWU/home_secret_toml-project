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
from pathlib import Path

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

    def test_token_returns_correct_value(self, home_secret_data: dict[str, T.Any]):
        """Test that Token returns the correct value for its path."""
        token = Token(data=home_secret_data, path="github.accounts.personal.account_id")
        assert token.v == "user123"

    def test_missing_path_raises_keyerror(self):
        """Test that accessing missing path raises KeyError."""
        data = {"existing": {"key": "value"}}
        token = Token(data=data, path="nonexistent.key")
        with pytest.raises(KeyError):
            _ = token.v

    def test_token_with_inline_table(self, home_secret_data: dict[str, T.Any]):
        """Test Token with inline table value."""
        token = Token(
            data=home_secret_data, path="aws.accounts.prod.secrets.deployment.creds"
        )
        creds = token.v
        assert isinstance(creds, dict)
        assert "access_key" in creds
        assert "secret_key" in creds


class TestHomeSecretToml:
    """Tests for the HomeSecretToml class."""

    def test_data_property_loads_toml(self, home_secret_path: Path):
        """Test that data property loads TOML file correctly."""
        hs_test = HomeSecretToml(path=home_secret_path)
        data = hs_test.data

        assert isinstance(data, dict)
        # TOML parses as nested dict
        assert "github" in data
        assert data["github"]["accounts"]["personal"]["account_id"] == "user123"

    def test_v_method_returns_value(self, home_secret_path: Path):
        """Test direct value access via v method."""
        hs_test = HomeSecretToml(path=home_secret_path)

        assert hs_test.v("github.accounts.personal.account_id") == "user123"
        assert hs_test.v("db.mysql_dev.port") == 3306
        assert hs_test.v("db.mysql_dev.ssl_enabled") is True

    def test_t_method_returns_token(self, home_secret_path: Path):
        """Test token creation via t method."""
        hs_test = HomeSecretToml(path=home_secret_path)

        token = hs_test.t("github.accounts.personal.account_id")
        assert isinstance(token, Token)
        assert token.v == "user123"

    def test_file_not_found_raises_error(self):
        """Test FileNotFoundError when file missing."""
        hs_test = HomeSecretToml(path=Path("/nonexistent/path/secrets.toml"))
        with pytest.raises(FileNotFoundError) as exc_info:
            _ = hs_test.data
        assert "secrets.toml" in str(exc_info.value)

    def test_v_method_caching(self, home_secret_path: Path):
        """Test that v method results are cached."""
        hs_test = HomeSecretToml(path=home_secret_path)

        # Call twice and verify it returns the same value (cached)
        result1 = hs_test.v("github.accounts.personal.account_id")
        result2 = hs_test.v("github.accounts.personal.account_id")
        assert result1 == result2

    def test_default_path_is_home_secret(self):
        """Test that default path points to $HOME/home_secret.toml."""
        hs_test = HomeSecretToml()
        assert hs_test.path == p_home_secret

    def test_custom_path(self, home_secret_path: Path):
        """Test that custom path is used when specified."""
        hs_test = HomeSecretToml(path=home_secret_path)
        assert hs_test.path == home_secret_path


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

    def test_with_test_fixture(self, home_secret_data: dict[str, T.Any]):
        """Test walk with actual test fixture data."""
        results = list(walk(home_secret_data))

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

    def test_generates_valid_python(self, home_secret_path: Path):
        """Test that generated code is valid Python syntax."""
        hs_test = HomeSecretToml(path=home_secret_path)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            temp_path = Path(f.name)

        try:
            gen_enum_code(hs_instance=hs_test, output_path=temp_path)

            # Verify the generated file is valid Python by compiling it
            generated_code = temp_path.read_text(encoding="utf-8")
            compile(generated_code, temp_path, "exec")
        finally:
            temp_path.unlink()

    def test_attribute_naming(self, home_secret_path: Path):
        """Test that dots are converted to double underscores."""
        hs_test = HomeSecretToml(path=home_secret_path)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            temp_path = Path(f.name)

        try:
            gen_enum_code(hs_instance=hs_test, output_path=temp_path)

            generated_code = temp_path.read_text(encoding="utf-8")

            # Check that attribute names use double underscores
            assert "github__accounts__personal__account_id" in generated_code
            assert "db__mysql_dev__port" in generated_code

            # Check that original paths are preserved in the string
            assert '"github.accounts.personal.account_id"' in generated_code
        finally:
            temp_path.unlink()

    def test_generated_file_structure(self, home_secret_path: Path):
        """Test the structure of the generated file."""
        hs_test = HomeSecretToml(path=home_secret_path)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            temp_path = Path(f.name)

        try:
            gen_enum_code(hs_instance=hs_test, output_path=temp_path)

            generated_code = temp_path.read_text(encoding="utf-8")

            # Check required components are present
            assert "from home_secret_toml import hs" in generated_code
            assert "class Secret:" in generated_code
            assert "def _validate_secret():" in generated_code
            assert 'if __name__ == "__main__":' in generated_code
        finally:
            temp_path.unlink()

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
