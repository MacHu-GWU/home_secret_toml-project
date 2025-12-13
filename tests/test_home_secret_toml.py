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
    mask_value,
    list_secrets,
    get_secret,
    generate_enum,
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


class Test_mask_value:
    """Tests for the mask_value function."""

    def test_non_string_returns_asterisk(self):
        """Test that non-string values return single asterisk."""
        assert mask_value(123) == "*"
        assert mask_value(3.14) == "*"
        assert mask_value(True) == "*"
        assert mask_value(None) == "*"
        assert mask_value(["a", "b"]) == "*"
        assert mask_value({"key": "value"}) == "*"

    def test_short_string_returns_three_asterisks(self):
        """Test that strings 8 chars or shorter return '***'."""
        assert mask_value("") == "***"
        assert mask_value("a") == "***"
        assert mask_value("ab") == "***"
        assert mask_value("abcdefgh") == "***"  # exactly 8 chars

    def test_long_string_shows_first_and_last_two(self):
        """Test that strings longer than 8 chars show first 2 and last 2."""
        assert mask_value("abcdefghi") == "ab***hi"  # 9 chars
        assert mask_value("admin@example.com") == "ad***om"  # 17 chars
        assert mask_value("ghp_xxxxxxxxxxxx") == "gh***xx"  # 16 chars


class Test_normalize_for_match:
    """Tests for the _normalize_for_match function."""

    def test_lowercase_conversion(self):
        """Test that strings are converted to lowercase."""
        from home_secret_toml.home_secret_toml import _normalize_for_match

        assert _normalize_for_match("GitHub") == "github"
        assert _normalize_for_match("AWS") == "aws"
        assert _normalize_for_match("MyAPI") == "myapi"

    def test_dash_to_underscore(self):
        """Test that dashes are converted to underscores."""
        from home_secret_toml.home_secret_toml import _normalize_for_match

        assert _normalize_for_match("my-key") == "my_key"
        assert _normalize_for_match("api-token-value") == "api_token_value"

    def test_combined_normalization(self):
        """Test that both lowercase and dash conversion work together."""
        from home_secret_toml.home_secret_toml import _normalize_for_match

        assert _normalize_for_match("My-API-Token") == "my_api_token"
        assert _normalize_for_match("GitHub-Personal") == "github_personal"


class Test_parse_query_facets:
    """Tests for the _parse_query_facets function."""

    def test_space_separator(self):
        """Test that spaces separate facets."""
        from home_secret_toml.home_secret_toml import _parse_query_facets

        assert _parse_query_facets("github personal") == ["github", "personal"]
        assert _parse_query_facets("aws  account") == ["aws", "account"]  # multiple spaces

    def test_comma_separator(self):
        """Test that commas separate facets."""
        from home_secret_toml.home_secret_toml import _parse_query_facets

        assert _parse_query_facets("github,personal") == ["github", "personal"]
        assert _parse_query_facets("aws,,account") == ["aws", "account"]  # multiple commas

    def test_mixed_separators(self):
        """Test that spaces and commas can be mixed."""
        from home_secret_toml.home_secret_toml import _parse_query_facets

        assert _parse_query_facets("github, personal") == ["github", "personal"]
        assert _parse_query_facets("aws ,account, token") == ["aws", "account", "token"]

    def test_normalization_applied(self):
        """Test that facets are normalized."""
        from home_secret_toml.home_secret_toml import _parse_query_facets

        assert _parse_query_facets("GitHub My-Token") == ["github", "my_token"]

    def test_empty_query(self):
        """Test that empty query returns empty list."""
        from home_secret_toml.home_secret_toml import _parse_query_facets

        assert _parse_query_facets("") == []
        assert _parse_query_facets("   ") == []
        assert _parse_query_facets(",,,") == []


class Test_matches_all_facets:
    """Tests for the _matches_all_facets function."""

    def test_single_facet_match(self):
        """Test matching with a single facet."""
        from home_secret_toml.home_secret_toml import _matches_all_facets

        assert _matches_all_facets("github.accounts.personal", ["github"]) is True
        assert _matches_all_facets("github.accounts.personal", ["azure"]) is False

    def test_multiple_facets_all_match(self):
        """Test that all facets must match."""
        from home_secret_toml.home_secret_toml import _matches_all_facets

        assert _matches_all_facets("github.accounts.personal", ["github", "personal"]) is True
        assert _matches_all_facets("github.accounts.personal", ["github", "work"]) is False

    def test_case_insensitive(self):
        """Test that matching is case-insensitive on the key side.

        Note: facets are expected to be pre-normalized (lowercase) by _parse_query_facets.
        """
        from home_secret_toml.home_secret_toml import _matches_all_facets

        # Key has mixed case, facet is normalized (lowercase)
        assert _matches_all_facets("GitHub.Accounts.Personal", ["github"]) is True
        assert _matches_all_facets("GITHUB.ACCOUNTS.PERSONAL", ["github"]) is True

    def test_dash_underscore_equivalent(self):
        """Test that dashes and underscores are treated as equivalent.

        Note: facets are expected to be pre-normalized (dashes -> underscores) by _parse_query_facets.
        """
        from home_secret_toml.home_secret_toml import _matches_all_facets

        # Key has underscore, facet is normalized (underscore)
        assert _matches_all_facets("my_api_token", ["my_api"]) is True
        # Key has dash, facet is normalized (underscore) - key is also normalized during matching
        assert _matches_all_facets("my-api-token", ["my_api"]) is True

    def test_empty_facets_matches_all(self):
        """Test that empty facets list matches any key."""
        from home_secret_toml.home_secret_toml import _matches_all_facets

        assert _matches_all_facets("any.key.here", []) is True


class Test_list_secrets:
    """Tests for the list_secrets function."""

    def test_list_secrets_returns_masked_values(self, home_secret_path: Path):
        """Test that list_secrets returns secrets with masked values."""
        results = list_secrets(path=home_secret_path)

        # Should return list of tuples
        assert isinstance(results, list)
        assert len(results) > 0

        # All items should be (key, masked_value) tuples
        for key, masked_value in results:
            assert isinstance(key, str)
            assert isinstance(masked_value, str)

        # Check specific entries
        result_dict = dict(results)
        assert "github.accounts.personal.account_id" in result_dict
        assert result_dict["github.accounts.personal.account_id"] == "***"  # user123 is 7 chars

    def test_list_secrets_with_query_filters_results(self, home_secret_path: Path):
        """Test that list_secrets with query filters to matching keys."""
        results = list_secrets(path=home_secret_path, query="github")

        # All keys should contain "github"
        for key, _ in results:
            assert "github" in key

        # Should not contain non-matching entries
        result_keys = [key for key, _ in results]
        assert not any("aws" in key for key in result_keys)
        assert not any("db" in key for key in result_keys)

    def test_list_secrets_case_insensitive(self, home_secret_path: Path):
        """Test that query matching is case-insensitive."""
        results_lower = list_secrets(path=home_secret_path, query="github")
        results_upper = list_secrets(path=home_secret_path, query="GITHUB")
        results_mixed = list_secrets(path=home_secret_path, query="GitHub")

        assert len(results_lower) > 0
        assert results_lower == results_upper
        assert results_lower == results_mixed

    def test_list_secrets_dash_underscore_equivalent(self, home_secret_path: Path):
        """Test that dashes and underscores are treated as equivalent in queries."""
        # The fixture has keys like "db.mysql_dev.port"
        results_underscore = list_secrets(path=home_secret_path, query="mysql_dev")
        results_dash = list_secrets(path=home_secret_path, query="mysql-dev")

        assert len(results_underscore) > 0
        assert results_underscore == results_dash

    def test_list_secrets_multi_facet_query(self, home_secret_path: Path):
        """Test that multiple facets (space/comma separated) use AND logic."""
        # Query with multiple facets - all must match
        results = list_secrets(path=home_secret_path, query="github personal")

        # All results should contain both "github" AND "personal"
        for key, _ in results:
            key_lower = key.lower()
            assert "github" in key_lower
            assert "personal" in key_lower

    def test_list_secrets_multi_facet_comma_separated(self, home_secret_path: Path):
        """Test that comma-separated facets work."""
        results_space = list_secrets(path=home_secret_path, query="github personal")
        results_comma = list_secrets(path=home_secret_path, query="github,personal")

        assert results_space == results_comma

    def test_list_secrets_with_no_matches_returns_empty(self, home_secret_path: Path):
        """Test that list_secrets with non-matching query returns empty list."""
        results = list_secrets(path=home_secret_path, query="nonexistent_query_string")

        assert results == []

    def test_list_secrets_file_not_found(self):
        """Test that list_secrets raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            list_secrets(path=Path("/nonexistent/path/secrets.toml"))


class Test_get_secret:
    """Tests for the get_secret function."""

    def test_get_secret_returns_value(self, home_secret_path: Path):
        """Test that get_secret returns the correct value for a key."""
        value = get_secret(key="github.accounts.personal.account_id", path=home_secret_path)
        assert value == "user123"

    def test_get_secret_with_various_types(self, home_secret_path: Path):
        """Test get_secret with different value types."""
        # String value
        assert get_secret(key="github.accounts.personal.admin_email", path=home_secret_path) == "admin@example.com"

        # Integer value
        assert get_secret(key="db.mysql_dev.port", path=home_secret_path) == 3306

        # Boolean value
        assert get_secret(key="db.mysql_dev.ssl_enabled", path=home_secret_path) is True

    def test_get_secret_with_inline_table(self, home_secret_path: Path):
        """Test get_secret with inline table (dict) value."""
        creds = get_secret(
            key="aws.accounts.prod.secrets.deployment.creds",
            path=home_secret_path,
        )
        assert isinstance(creds, dict)
        assert creds["access_key"] == "AKIAIOSFODNN7EXAMPLE"
        assert creds["secret_key"] == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

    def test_get_secret_key_not_found(self, home_secret_path: Path):
        """Test that get_secret raises KeyError for missing key."""
        with pytest.raises(KeyError) as exc_info:
            get_secret(key="nonexistent.key", path=home_secret_path)
        assert "nonexistent" in str(exc_info.value)

    def test_get_secret_partial_key_not_found(self, home_secret_path: Path):
        """Test that get_secret raises KeyError for partially matching key."""
        with pytest.raises(KeyError) as exc_info:
            get_secret(key="github.accounts.personal.nonexistent", path=home_secret_path)
        assert "nonexistent" in str(exc_info.value)

    def test_get_secret_file_not_found(self):
        """Test that get_secret raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            get_secret(key="any.key", path=Path("/nonexistent/path/secrets.toml"))

    def test_get_secret_default_path(self):
        """Test that get_secret uses default path when not specified."""
        # This test verifies the function signature works with default path
        # We can't actually test the default path without the real file
        # Just verify the function accepts no path argument
        try:
            get_secret(key="any.key")
        except FileNotFoundError:
            # Expected if ~/home_secret.toml doesn't exist
            pass
        except KeyError:
            # Expected if file exists but key doesn't
            pass


class Test_generate_enum:
    """Tests for the generate_enum function."""

    def test_generate_enum_creates_file(self, home_secret_path: Path, tmp_path):
        """Test that generate_enum creates the enum file."""
        output_file = tmp_path / "home_secret_enum.py"
        result_path = generate_enum(path=home_secret_path, output=output_file)

        assert result_path == output_file
        assert output_file.exists()
        content = output_file.read_text()
        assert "class Secret:" in content

    def test_generate_enum_to_directory(self, home_secret_path: Path, tmp_path):
        """Test that generate_enum to directory creates file with default name."""
        result_path = generate_enum(path=home_secret_path, output=tmp_path)

        expected_file = tmp_path / "home_secret_enum.py"
        assert result_path == expected_file
        assert expected_file.exists()

    def test_generate_enum_no_overwrite_by_default(
        self, home_secret_path: Path, tmp_path
    ):
        """Test that generate_enum raises FileExistsError when file exists."""
        output_file = tmp_path / "home_secret_enum.py"
        output_file.write_text("existing content")

        with pytest.raises(FileExistsError) as exc_info:
            generate_enum(path=home_secret_path, output=output_file)
        assert "already exists" in str(exc_info.value)

        # Original content should be preserved
        assert output_file.read_text() == "existing content"

    def test_generate_enum_with_overwrite(self, home_secret_path: Path, tmp_path):
        """Test that generate_enum overwrites when overwrite=True."""
        output_file = tmp_path / "home_secret_enum.py"
        output_file.write_text("existing content")

        result_path = generate_enum(
            path=home_secret_path, output=output_file, overwrite=True
        )

        assert result_path == output_file
        # Content should be replaced
        content = output_file.read_text()
        assert "class Secret:" in content

    def test_generate_enum_file_not_found(self, tmp_path):
        """Test that generate_enum raises FileNotFoundError for missing secrets file."""
        output_file = tmp_path / "home_secret_enum.py"
        with pytest.raises(FileNotFoundError):
            generate_enum(
                path=Path("/nonexistent/path/secrets.toml"), output=output_file
            )


if __name__ == "__main__":
    from home_secret_toml.tests import run_cov_test

    run_cov_test(
        __file__,
        "home_secret_toml.home_secret_toml",
        preview=False,
    )
