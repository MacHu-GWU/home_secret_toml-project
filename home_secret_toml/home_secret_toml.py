# -*- coding: utf-8 -*-

"""
Home Secrets Management Module (TOML Version)

This module provides a flexible and secure mechanism for loading secrets from a TOML file.
It implements a flat key-value structure for easy navigation and editing, with lazy loading
of secrets and automatic synchronization between development and runtime environments.

**Architecture Overview**

The module is built around three core concepts:

1. **Flat Structure**: All secrets are stored as flat key-value pairs with dot-separated keys
2. **Lazy Loading**: Secrets are only loaded from disk when actually accessed
3. **Token System**: Values are represented as tokens that resolve to actual values on demand

**File Location Strategy**

By default, the secret file is expected to be located at ``${HOME}/home_secret.toml``.
You can also specify a custom path when creating a HomeSecretToml instance.

**Key Features**

- **Flat Key Structure**: Each key contains the full path, making context immediately visible
- **Comment Support**: TOML natively supports # comments for documentation
- **Lazy Loading**: Secrets are only read from disk when accessed via ``.v`` property
- **Token-based Access**: Flexible reference system for delayed value resolution
- **Robust Error Handling**: Clear error messages for missing or malformed secrets
- **IDE Support**: Generated enum class provides full autocomplete support
- **Configurable Path**: Custom secret file path can be specified for testing

**Direct value access**::

    # Get a secret value immediately
    api_key = hs.v("github.accounts.personal.users.dev.secrets.api_token.value")

**Token-based access**::

    # Create a token for later use
    token = hs.t("github.accounts.personal.users.dev.secrets.api_token.value")
    # Resolve the token when needed
    api_key = token.v

**Custom path for testing**::

    # Use a custom path for testing
    hs_test = HomeSecretToml(path=Path("/path/to/test/secrets.toml"))
"""

import typing as T
import sys
import argparse
import tomllib
import textwrap
import dataclasses
from pathlib import Path
from functools import cached_property

__version__ = "0.1.1"
__license__ = "MIT"
__author__ = "Sanhe Hu"

# Configuration: Secret file name
filename = "home_secret.toml"

# Default runtime location: Home directory secrets file
p_home_secret = Path.home() / filename

# Path to the generated enum file containing flat attribute access to all secrets
# This file is auto-generated and provides a simple dot-notation alternative
p_here_enum = Path("home_secret_enum.py")


def _deep_get(
    dct: dict,
    path: str,
) -> T.Any:
    """
    Retrieve a nested value from a dictionary using dot-separated path notation.

    This function enables accessing deeply nested dictionary values using a simple
    string path like "github.accounts.personal.account_id". Since TOML parses
    dotted keys as nested dictionaries, this function traverses the nested structure.

    :param dct: The dictionary to search through
    :param path: Dot-separated path to the desired value (e.g., "github.accounts.personal.account_id")

    :raises KeyError: When any part of the path doesn't exist in the dictionary

    :return: The value found at the specified path
    """
    value = dct  # Start with the root dictionary
    parts = list()
    # Navigate through each part of the dot-separated path
    for part in path.split("."):
        parts.append(part)
        if isinstance(value, dict) and part in value:
            value = value[part]  # Move deeper into the nested structure
        else:
            # Provide clear error message showing exactly what key was missing
            current_path = ".".join(parts)
            raise KeyError(f"Key {current_path!r} not found in the provided data.")
    return value


@dataclasses.dataclass
class Token:
    """
    A lazy-loading token that represents a reference to a secret value.

    Tokens are placeholders for values that aren't resolved when the token object
    is created. Instead, the actual secret value is loaded from the TOML file
    only when accessed via the ``.v`` property. This enables:

    - **Deferred Loading**: Values are only read from disk when actually needed
    - **Reference Flexibility**: Tokens can be passed around and stored before resolution
    - **Error Isolation**: TOML parsing errors only occur when values are accessed

    :param data: Reference to the loaded TOML data dictionary
    :param path: Dot-separated path to the secret value within the TOML structure
    """

    data: dict[str, T.Any] = dataclasses.field()
    path: str = dataclasses.field()

    @property
    def v(self) -> T.Any:
        """
        Lazily load and return the secret value from the TOML data.

        :return: The secret value at the specified path
        """
        return _deep_get(dct=self.data, path=self.path)


@dataclasses.dataclass
class HomeSecretToml:
    """
    Main interface for loading and accessing secrets from a home_secret.toml file.

    This class provides the core functionality for the secrets management system:

    - **Configurable Path**: Specify custom path for testing or different environments
    - **Lazy Loading**: TOML is only parsed when first accessed
    - **Caching**: Parsed TOML data is cached for subsequent access
    - **Flexible Access**: Supports both direct value access and token creation

    :param path: Path to the TOML secrets file. Defaults to $HOME/home_secret.toml
    """

    path: Path = dataclasses.field(default_factory=lambda: p_home_secret)
    _cache_v: dict[str, T.Any] = dataclasses.field(default_factory=dict, repr=False)
    _cache_t: dict[str, Token] = dataclasses.field(default_factory=dict, repr=False)

    @cached_property
    def data(self) -> dict[str, T.Any]:
        """
        Load and cache the secret data from the TOML file.

        :raises FileNotFoundError: If the secrets file does not exist at the specified path
        """
        if not self.path.exists():
            raise FileNotFoundError(f"Secret file not found at {self.path}")
        return tomllib.loads(self.path.read_text(encoding="utf-8"))

    def v(self, path: str) -> T.Any:
        """
        Direct access to secret values using dot-separated path notation.

        This method provides immediate access to secret values without creating
        intermediate token objects. It's the most direct way to retrieve secrets
        when you need the value immediately.

        .. note::

            V stands for Value.
        """
        if path not in self._cache_v:
            self._cache_v[path] = _deep_get(dct=self.data, path=path)
        return self._cache_v[path]

    def t(self, path: str) -> Token:
        """
        Create a Token object for deferred access to secret values.

        This method creates a token that can be stored, passed around, and resolved
        later when the actual value is needed. This is useful for:

        - **Configuration Objects**: Store tokens in config classes
        - **Dependency Injection**: Pass tokens to components that resolve them later
        - **Conditional Access**: Create tokens but only resolve them when needed

        .. note::

            T stands for Token.
        """
        if path not in self._cache_t:
            self._cache_t[path] = Token(
                data=self.data,
                path=path,
            )
        return self._cache_t[path]


# Global instance: Single shared secrets manager for the entire application
# This follows the singleton pattern to ensure consistent access to secrets
# across all modules that import this file
# Uses the default path: $HOME/home_secret.toml
hs = HomeSecretToml()

UNKNOWN = "..."
DESCRIPTION = "description"
TAB = " " * 4


def walk(
    dct: dict[str, T.Any],
    _parent_path: str = "",
) -> T.Iterable[tuple[str, T.Any]]:
    """
    Recursively traverse a nested dictionary structure to extract all leaf paths and values.

    This function performs a depth-first traversal of the secrets TOML structure,
    yielding dot-separated paths to all non-dictionary values while filtering out
    metadata fields and placeholder values.

    **Filtering Logic**:

    - Recursively descends into dictionary values
    - Skips 'description' keys (metadata)
    - Skips values equal to UNKNOWN ("..." placeholder)
    - Yields complete dot-separated paths for all other leaf values

    :param dct: Dictionary to traverse (typically the loaded secrets TOML)
    :param _parent_path: Current path prefix for recursive calls (internal use)

    :yields: Tuples of (path, value) where path is dot-separated and value is the leaf data

    Example::

        data = {
            "github": {
                "description": "GitHub platform",  # Skipped (description)
                "accounts": {
                    "personal": {
                        "account_id": "user123",
                        "admin_email": "...",  # Skipped (UNKNOWN)
                    }
                }
            }
        }

        # Results in:
        # ("github.accounts.personal.account_id", "user123")
    """
    for key, value in dct.items():
        path = f"{_parent_path}.{key}" if _parent_path else key
        if isinstance(value, dict):
            yield from walk(
                dct=value,
                _parent_path=path,
            )
        elif key == DESCRIPTION:
            continue
        elif value == UNKNOWN:
            continue
        else:
            yield path, value


def gen_enum_code(
    hs_instance: HomeSecretToml | None = None,
    output_path: Path | None = None,
) -> None:
    """
    Generate a flat enumeration class providing direct attribute access to all secrets.

    This function creates an alternative access pattern by generating a flat class
    where each secret path becomes a simple attribute name. The generated code provides:

    - **Flat Access**: All secrets accessible as `Secret.github__accounts__personal__...`
    - **Auto-Generation**: Automatically discovers all paths in the TOML structure
    - **Validation Function**: Includes a function to test all generated paths
    - **Simple Imports**: Minimal dependencies for the generated file

    **Path Transformation Logic**:

    - Converts dots to double underscores for valid Python identifiers
    - Preserves the complete path hierarchy in the attribute name

    :param hs_instance: HomeSecretToml instance to use for reading secrets.
                        Defaults to the global hs instance.
    :param output_path: Path to write the generated file. Defaults to ./home_secret_enum.py
    """
    if hs_instance is None:
        hs_instance = hs
    if output_path is None:
        output_path = p_here_enum

    # Build the generated file content line by line
    lines = [
        textwrap.dedent(
            """
        try:
            from home_secret_toml import hs
        except ImportError:  # pragma: no cover
            pass


        class Secret:
            # fmt: off
        """
        )
    ]

    # Extract all secret paths from the loaded TOML data
    path_list = [path for path, _ in walk(hs_instance.data)]

    # Generate an attribute for each discovered secret path
    for path in path_list:
        # Transform the path into a valid Python attribute name
        # Convert dots to double underscores
        attr_name = path.replace(".", "__")
        lines.append(f'{TAB}{attr_name} = hs.t("{path}")')

    # Add validation function and main block to the generated file
    lines.append(
        textwrap.dedent(
            """
            # fmt: on


        def _validate_secret():
            print("Validate secret:")
            for key, token in Secret.__dict__.items():
                if key.startswith("_") is False:
                    print(f"{key} = {token.v}")


        if __name__ == "__main__":
            _validate_secret()
        """
        )
    )
    # Write the generated code to the enum file
    output_path.write_text("\n".join(lines), encoding="utf-8")


# ------------------------------------------------------------------------------
# CLI Functions
# ------------------------------------------------------------------------------
def mask_value(value: T.Any) -> str:
    """
    Mask a secret value for safe display.

    **Masking Rules**:

    - Non-string values: replaced with "*"
    - Strings longer than 8 characters: show first 2 and last 2 chars with "***" in between
    - Strings 8 characters or shorter: replaced with "***"

    :param value: The value to mask

    :return: Masked string representation
    """
    if not isinstance(value, str):
        return "*"
    if len(value) > 8:
        return f"{value[:2]}***{value[-2:]}"
    else:
        return "***"


def _normalize_for_match(s: str) -> str:
    """
    Normalize a string for matching by converting to lowercase and replacing dashes with underscores.

    :param s: The string to normalize

    :return: Normalized string
    """
    return s.lower().replace("-", "_")


def _parse_query_facets(query: str) -> list[str]:
    """
    Parse a query string into individual search facets.

    Splits on spaces and commas, filters empty strings, and normalizes each facet.

    :param query: The query string to parse

    :return: List of normalized facets
    """
    # Replace commas with spaces, then split on whitespace
    parts = query.replace(",", " ").split()
    # Normalize each non-empty part
    return [_normalize_for_match(part) for part in parts if part]


def _matches_all_facets(key: str, facets: list[str]) -> bool:
    """
    Check if a key matches all search facets.

    :param key: The key to check (will be normalized)
    :param facets: List of normalized facets that must all be substrings

    :return: True if all facets are found in the normalized key
    """
    normalized_key = _normalize_for_match(key)
    return all(facet in normalized_key for facet in facets)


def list_secrets(
    path: Path | None = None,
    query: str | None = None,
) -> list[tuple[str, str]]:
    """
    List all secrets with masked values.

    This is the underlying function for the ``hst ls`` command.

    **Query Matching Rules**:

    - Case-insensitive matching
    - Dashes (-) and underscores (_) are treated as equivalent
    - Spaces and commas in query are treated as separators for multiple facets
    - All facets must match (AND logic) for a key to be included

    :param path: Path to the TOML secrets file. Defaults to $HOME/home_secret.toml
    :param query: Optional query string to filter keys. Supports multiple facets
        separated by spaces or commas.

    :return: List of (key, masked_value) tuples
    """
    if path is None:
        path = p_home_secret

    hs_instance = HomeSecretToml(path=path)
    data = hs_instance.data

    results = list(walk(data))

    if query:
        facets = _parse_query_facets(query)
        if facets:
            results = [(key, value) for key, value in results if _matches_all_facets(key, facets)]

    return [(key, mask_value(value)) for key, value in results]


def cmd_ls(
    path: Path | None = None,
    query: str | None = None,
) -> None:  # pragma: no cover
    """
    CLI wrapper for list_secrets. Prints results to stdout.

    :param path: Path to the TOML secrets file. Defaults to $HOME/home_secret.toml
    :param query: Optional substring to filter keys
    """
    try:
        results = list_secrets(path=path, query=query)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if not results:
        if query:
            print(f'No secrets found matching "{query}"')
        else:
            print("No secrets found")
        return

    for key, masked_value in results:
        print(f'{key} = "{masked_value}"')


def generate_enum(
    path: Path | None = None,
    output: Path | None = None,
    overwrite: bool = False,
) -> Path:
    """
    Generate the home_secret_enum.py file.

    This is the underlying function for the ``hst gen-enum`` command.

    :param path: Path to the TOML secrets file. Defaults to $HOME/home_secret.toml
    :param output: Output path (directory or file). Defaults to ./home_secret_enum.py
    :param overwrite: If True, allow overwriting existing files

    :raises FileExistsError: If output file exists and overwrite is False
    :raises FileNotFoundError: If secrets file does not exist

    :return: The path where the enum file was written
    """
    if path is None:
        path = p_home_secret

    # Determine output path
    if output is None:
        output_path = Path("home_secret_enum.py")
    else:
        output_path = output
        if output_path.is_dir():
            output_path = output_path / "home_secret_enum.py"
        elif not output_path.suffix == ".py":
            # Treat as directory if not ending with .py
            output_path = output_path / "home_secret_enum.py"

    # Check if file exists and handle overwrite logic
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"{output_path} already exists. Use --overwrite to replace it."
        )

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    hs_instance = HomeSecretToml(path=path)
    gen_enum_code(hs_instance=hs_instance, output_path=output_path)

    return output_path


def cmd_gen_enum(
    path: Path | None = None,
    output: Path | None = None,
    overwrite: bool = False,
) -> None:  # pragma: no cover
    """
    CLI wrapper for generate_enum. Prints result to stdout.

    :param path: Path to the TOML secrets file. Defaults to $HOME/home_secret.toml
    :param output: Output path (directory or file). Defaults to ./home_secret_enum.py
    :param overwrite: If True, allow overwriting existing files
    """
    try:
        output_path = generate_enum(path=path, output=output, overwrite=overwrite)
        print(f"Generated: {output_path}")
    except FileExistsError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)


def main() -> None:  # pragma: no cover
    """
    Main CLI entry point for the hst command.
    """
    parser = argparse.ArgumentParser(
        prog="hst",
        description="Home Secret TOML - Local credential management CLI",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ls subcommand
    ls_parser = subparsers.add_parser(
        "ls",
        help="List secrets with masked values",
    )
    ls_parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Path to the TOML secrets file. Defaults to ~/home_secret.toml",
    )
    ls_parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Optional substring to filter secret keys",
    )

    # gen-enum subcommand
    gen_enum_parser = subparsers.add_parser(
        "gen-enum",
        help="Generate home_secret_enum.py file",
    )
    gen_enum_parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Path to the TOML secrets file. Defaults to ~/home_secret.toml",
    )
    gen_enum_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path (directory or .py file). Defaults to ./home_secret_enum.py",
    )
    gen_enum_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing file",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)
    elif args.command == "ls":
        cmd_ls(path=args.path, query=args.query)
    elif args.command == "gen-enum":
        cmd_gen_enum(path=args.path, output=args.output, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
