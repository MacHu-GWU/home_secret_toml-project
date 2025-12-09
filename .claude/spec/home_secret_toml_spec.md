# HOME Secret TOML Specification

## 1. Overview

HOME Secret TOML is a local credential management system that stores sensitive development credentials in a structured TOML configuration file. It provides a flat, human-readable format for organizing secrets across multiple service providers, accounts, and users, with Python integration for secure programmatic access.

**Dual Usage Modes**:

- **Single-File Distribution**: The `home_secret_toml.py` module is self-contained and can be directly copied into any project. It has zero external dependencies (uses only Python 3.11+ standard library).
- **Package Installation**: Install via `pip install home_secret_toml` for use as a proper Python package with CLI support.

## 2. Core Philosophy

### 2.1 Flat Key Structure

Unlike hierarchical JSON configurations where nested structures make it difficult to track context, HOME Secret TOML enforces a **flat key-value structure**. Every secret is represented as a single line where the full path is embedded in the key itself:

```toml
github.accounts.personal.users.dev.secrets.api_token.value = "ghp_xxxx"
```

This design choice provides:

- **Immediate Context**: Each line clearly shows the provider, account, user, and secret being edited
- **Easy Navigation**: Text search instantly locates any credential
- **Comment Support**: TOML natively supports `#` comments for documentation
- **Reduced Complexity**: No nested brackets or indentation to manage

**Note**: While TOML keys appear flat in the file, the TOML parser interprets dotted keys as nested dictionaries internally. The library handles this transparently.

### 2.2 Alias-Based Security

All keys in the configuration file use **non-sensitive aliases** rather than real identifiers:

- Provider aliases (e.g., `github`, `aws_prod`)
- Account aliases (e.g., `personal`, `company_main`)
- User aliases (e.g., `dev`, `admin`)
- Secret aliases (e.g., `api_token`, `db_password`)

This ensures that even if the key structure is exposed (e.g., in generated code or logs), no sensitive information is revealed. The actual sensitive data exists only in the values.

### 2.3 Single Source of Truth

All credentials consolidate into a single file located at `$HOME/home_secret.toml`. This eliminates:

- Scattered credential fragments across projects
- Environment variable duplication
- Inconsistent credential storage patterns

### 2.4 Zero External Dependencies

The library uses only Python 3.11+ standard library modules:

- `tomllib` for TOML parsing (built into Python 3.11+)
- `dataclasses` for data structures
- `pathlib` for path handling
- `argparse` for CLI
- `typing` for type hints

This ensures the single-file distribution works without any `pip install`.

## 3. File Format Specification

### 3.1 File Location

The primary secrets file MUST be located at:

```
$HOME/home_secret.toml
```

Where `$HOME` represents the user's home directory (e.g., `/Users/username` on macOS, `/home/username` on Linux, `C:\Users\username` on Windows).

A custom path can be specified when creating a `HomeSecretToml` instance for testing or alternative configurations.

### 3.2 Key Format

Keys follow a dot-separated path notation with the following constraints:

- Keys contain only lowercase letters, numbers, and underscores
- Path segments are separated by dots (`.`)
- Keys are case-sensitive

Valid key patterns:

```
<provider>.<attribute> = <value>
<provider>.accounts.<account>.<attribute> = <value>
<provider>.accounts.<account>.secrets.<secret>.<attribute> = <value>
<provider>.accounts.<account>.users.<user>.<attribute> = <value>
<provider>.accounts.<account>.users.<user>.secrets.<secret>.<attribute> = <value>
```

### 3.3 Value Types

HOME Secret TOML supports the following TOML value types:

| Type | Example | Use Case |
|------|---------|----------|
| String | `"ghp_xxxx"` | API keys, passwords, tokens |
| Integer | `5432` | Port numbers |
| Boolean | `true` | Feature flags |
| Inline Table | `{ key1 = "v1", key2 = "v2" }` | Structured credentials (e.g., OAuth creds) |
| Array | `["scope1", "scope2"]` | Permission lists |

### 3.4 Hierarchical Structure

The logical hierarchy follows this pattern:

```
Provider
├── Provider Attributes (description, etc.)
└── accounts
    └── Account
        ├── Account Attributes (account_id, admin_email, etc.)
        ├── secrets (account-level secrets)
        │   └── Secret
        │       └── Secret Attributes (name, value, creds, etc.)
        └── users
            └── User
                ├── User Attributes (user_id, email, etc.)
                └── secrets (user-level secrets)
                    └── Secret
                        └── Secret Attributes (name, value, creds, etc.)
```

### 3.5 Standard Attributes

While the system is flexible and allows arbitrary attributes, the following are conventionally used:

**Provider Level:**
- `<provider>.description` - Human-readable description of the provider

**Account Level:**
- `<provider>.accounts.<account>.account_id` - Provider-specific account identifier
- `<provider>.accounts.<account>.admin_email` - Administrator email for the account
- `<provider>.accounts.<account>.description` - Human-readable description

**User Level:**
- `<provider>.accounts.<account>.users.<user>.user_id` - Provider-specific user identifier
- `<provider>.accounts.<account>.users.<user>.email` - User email address
- `<provider>.accounts.<account>.users.<user>.description` - Human-readable description

**Secret Level:**
- `<secret>.name` - Human-readable name of the secret
- `<secret>.value` - The actual secret value (API key, password, token, etc.)
- `<secret>.description` - Human-readable description of the secret's purpose
- `<secret>.creds` - Inline table for multi-part credentials (e.g., `{ access_key = "...", secret_key = "..." }`)

### 3.6 Example Configuration

```toml
# ------------------------------------------------------------------------------
# @GitHub
# ------------------------------------------------------------------------------
github.description = "GitHub code hosting platform"

# Personal account
github.accounts.personal.account_id = "machuuser"
github.accounts.personal.admin_email = "user@example.com"
github.accounts.personal.description = "Personal GitHub account"

github.accounts.personal.users.dev.user_id = "12345678"
github.accounts.personal.users.dev.email = "user@example.com"
github.accounts.personal.users.dev.secrets.api_token.name = "Development Token"
github.accounts.personal.users.dev.secrets.api_token.value = "ghp_xxxxxxxxxxxx"
github.accounts.personal.users.dev.secrets.api_token.description = "Full repo access token"

# ------------------------------------------------------------------------------
# @AWS
# ------------------------------------------------------------------------------
aws.description = "Amazon Web Services"

aws.accounts.prod.account_id = "123456789012"
aws.accounts.prod.admin_email = "admin@company.com"
aws.accounts.prod.description = "Production AWS account"

# Account-level secret (not tied to a specific user)
aws.accounts.prod.secrets.deployment_key.name = "Deployment Access Key"
aws.accounts.prod.secrets.deployment_key.value = "AKIAXXXXXXXXXX"
aws.accounts.prod.secrets.deployment_key.creds = { access_key = "AKIAXXXXXXXXXX", secret_key = "xxxxxxxxxxxxxxxxxxxxxxxx" }

# User-level secret
aws.accounts.prod.users.ci_bot.user_id = "AIDAXXXXXXXXXX"
aws.accounts.prod.users.ci_bot.email = "ci@company.com"
aws.accounts.prod.users.ci_bot.secrets.deploy.name = "CI Deployment Credentials"
aws.accounts.prod.users.ci_bot.secrets.deploy.value = "AKIAXXXXXXXXXX"
aws.accounts.prod.users.ci_bot.secrets.deploy.creds = { access_key = "AKIAXXXXXXXXXX", secret_key = "xxxxxxxxxxxxxxxxxxxxxxxx" }
```

## 4. Python API Specification

### 4.1 HomeSecretToml Class

The `HomeSecretToml` class is the primary interface for loading and accessing secrets from the TOML file. It is implemented as a `@dataclass`.

#### 4.1.1 Constructor

```python
@dataclass
class HomeSecretToml:
    """
    Main interface for loading and accessing secrets from a home_secret.toml file.

    Args:
        path: Path to the TOML secrets file.
              Defaults to $HOME/home_secret.toml
    """
    path: Path = field(default_factory=lambda: p_home_secret)
```

#### 4.1.2 Properties

**`data`** (read-only, cached)

```python
@cached_property
def data(self) -> dict[str, Any]:
    """
    Load and cache the secret data from the TOML file.

    Returns:
        A nested dictionary representation of the TOML file.
        TOML parses dotted keys like "a.b.c" as nested dicts {"a": {"b": {"c": value}}}.

    Raises:
        FileNotFoundError: If the secrets file does not exist

    Note:
        This property is lazy-loaded and cached via @cached_property.
        The file is only read from disk on first access.
    """
```

#### 4.1.3 Methods

**`v(path: str) -> Any`**

```python
def v(self, path: str) -> Any:
    """
    Direct access to secret values using dot-separated path notation.

    Args:
        path: Dot-separated path to the secret value
              (e.g., "github.accounts.personal.users.dev.secrets.api_token.value")

    Returns:
        The secret value at the specified path (string, int, bool, dict, or list)

    Raises:
        KeyError: If the specified path does not exist in the data

    Note:
        V stands for "Value". Results are cached in an internal dictionary
        for performance on repeated access.
    """
```

**`t(path: str) -> Token`**

```python
def t(self, path: str) -> Token:
    """
    Create a Token object for deferred access to secret values.

    Args:
        path: Dot-separated path to the secret value

    Returns:
        A Token object that can be resolved later via its .v property

    Note:
        T stands for "Token". Tokens are cached in an internal dictionary.
        Useful for dependency injection and configuration objects where
        value resolution should be deferred.
    """
```

### 4.2 Token Class

The `Token` class represents a lazy reference to a secret value. It is implemented as a `@dataclass`.

```python
@dataclass
class Token:
    """
    A lazy-loading token that represents a reference to a secret value.

    Attributes:
        data: Reference to the loaded TOML data dictionary
        path: Dot-separated path to the secret value
    """
    data: dict[str, Any]
    path: str

    @property
    def v(self) -> Any:
        """
        Lazily resolve and return the secret value.

        Returns:
            The secret value at the specified path

        Raises:
            KeyError: If the path does not exist
        """
```

### 4.3 Global Instance

The module provides a pre-configured global instance for convenience:

```python
hs = HomeSecretToml()
```

This allows simple usage patterns:

```python
from home_secret_toml import hs

api_key = hs.v("github.accounts.personal.users.dev.secrets.api_token.value")
```

### 4.4 Enum Code Generation

The library provides functions to generate a Python module containing enumerated access to all secrets.

**`gen_enum_code(hs_instance: HomeSecretToml | None = None, output_path: Path | None = None) -> None`**

Low-level function that generates the enum code file.

**`generate_enum(path: Path | None = None, output: Path | None = None, overwrite: bool = False) -> Path`**

High-level function for the CLI that handles path resolution and error checking.

```python
def generate_enum(
    path: Path | None = None,
    output: Path | None = None,
    overwrite: bool = False,
) -> Path:
    """
    Generate the home_secret_enum.py file.

    Args:
        path: Path to the TOML secrets file. Defaults to $HOME/home_secret.toml
        output: Output path (directory or file). Defaults to ./home_secret_enum.py
                If a directory is provided, creates home_secret_enum.py in that directory.
        overwrite: If True, allow overwriting existing files

    Returns:
        The path where the enum file was written

    Raises:
        FileExistsError: If output file exists and overwrite is False
        FileNotFoundError: If secrets file does not exist
    """
```

#### 4.4.1 Generated Code Format

Given a TOML file with:

```toml
github.accounts.personal.users.dev.secrets.api_token.value = "ghp_xxxx"
aws.accounts.prod.secrets.deploy.creds = { access_key = "AKIA...", secret_key = "xxxx" }
```

The generated code SHALL be:

```python
try:
    from home_secret_toml import hs
except ImportError:
    pass


class Secret:
    # fmt: off
    github__accounts__personal__users__dev__secrets__api_token__value = hs.t("github.accounts.personal.users.dev.secrets.api_token.value")
    aws__accounts__prod__secrets__deploy__creds = hs.t("aws.accounts.prod.secrets.deploy.creds")
    # fmt: on


def _validate_secret():
    """Validate all secret paths by resolving their values."""
    print("Validate secret:")
    for key, token in Secret.__dict__.items():
        if not key.startswith("_"):
            print(f"{key} = {token.v}")


if __name__ == "__main__":
    _validate_secret()
```

#### 4.4.2 Path Transformation Rules

The transformation from TOML path to Python attribute name:

| TOML Path | Python Attribute |
|-----------|------------------|
| `github.accounts.personal.users.dev.secrets.api_token.value` | `github__accounts__personal__users__dev__secrets__api_token__value` |
| `aws.accounts.prod.account_id` | `aws__accounts__prod__account_id` |

Rules:
1. All dots (`.`) are replaced with double underscores (`__`)
2. The full path is preserved

#### 4.4.3 Filtering Rules

The following entries SHALL be excluded from the generated enum:

1. Entries where the value equals the placeholder string `"..."`
2. Entries where the key ends with `.description` (metadata only)

### 4.5 Helper Functions

**`walk(dct: dict, _parent_path: str = "") -> Iterable[tuple[str, Any]]`**

Recursively traverses a nested dictionary and yields all leaf paths and values. Filters out `description` keys and placeholder values (`"..."`).

**`list_secrets(path: Path | None = None, query: str | None = None) -> list[tuple[str, str]]`**

Lists all secrets with masked values. This is the underlying function for the `hst ls` CLI command.

**`mask_value(value: Any) -> str`**

Masks a secret value for safe display:
- Non-string values: `"*"`
- Strings ≤ 8 characters: `"***"`
- Strings > 8 characters: `"ab***yz"` (first 2 and last 2 chars shown)

## 5. Command-Line Interface (CLI)

The library provides a CLI tool `hst` (Home Secret TOML) for managing secrets from the command line.

### 5.1 Installation

The CLI is available after installing the package:

```bash
pip install home_secret_toml
hst --help
```

### 5.2 Global Options

```
hst --version    Show version information
hst --help       Show help message
```

### 5.3 Commands

#### 5.3.1 `hst ls` - List Secrets

List all secrets with their values masked for security.

```bash
hst ls [--path PATH] [--query QUERY]
```

**Options:**
- `--path PATH`: Path to the TOML secrets file. Defaults to `~/home_secret.toml`
- `--query QUERY`: Filter secrets by key substring

**Query Matching Rules:**
- Case-insensitive matching
- Dashes (`-`) and underscores (`_`) are treated as equivalent
- Spaces and commas in query are treated as separators for multiple facets
- All facets must match (AND logic) for a key to be included

**Examples:**

```bash
# List all secrets
hst ls

# List secrets from a custom file
hst ls --path /path/to/secrets.toml

# Filter by single term (case-insensitive)
hst ls --query github
hst ls --query GITHUB

# Filter with multiple terms (AND logic)
hst ls --query "github personal"
hst ls --query "github,personal"

# Dash and underscore are equivalent
hst ls --query "mysql-dev"   # matches mysql_dev
hst ls --query "mysql_dev"   # matches mysql-dev
```

**Output Format:**

```
github.accounts.personal.account_id = "***"
github.accounts.personal.users.dev.secrets.api_token.value = "gh***xx"
aws.accounts.prod.account_id = "*"
```

#### 5.3.2 `hst gen-enum` - Generate Enum File

Generate a Python file with enumerated access to all secrets.

```bash
hst gen-enum [--path PATH] [--output OUTPUT] [--overwrite]
```

**Options:**
- `--path PATH`: Path to the TOML secrets file. Defaults to `~/home_secret.toml`
- `--output OUTPUT`: Output path (directory or .py file). Defaults to `./home_secret_enum.py`
- `--overwrite`: Overwrite existing file if it exists

**Examples:**

```bash
# Generate enum file in current directory
hst gen-enum

# Generate from custom secrets file
hst gen-enum --path /path/to/secrets.toml

# Generate to a specific location
hst gen-enum --output /path/to/output.py

# Generate to a directory (creates home_secret_enum.py in that directory)
hst gen-enum --output /path/to/dir/

# Overwrite existing file
hst gen-enum --overwrite
```

## 6. Usage Scenarios

### 6.1 Single-File Distribution (Copy-Paste)

For projects where you want to avoid adding dependencies:

1. Copy `home_secret_toml/home_secret_toml.py` to your project
2. Import and use directly:

```python
from home_secret_toml import hs

api_key = hs.v("github.accounts.personal.users.dev.secrets.api_token.value")
```

**Requirements:**
- Python 3.11+ (for `tomllib` standard library)
- No pip install needed

### 6.2 Package Installation

For projects that prefer proper package management:

```bash
pip install home_secret_toml
```

```python
from home_secret_toml import hs

api_key = hs.v("github.accounts.personal.users.dev.secrets.api_token.value")
```

**Benefits:**
- CLI tool `hst` available
- Proper package structure
- Easy updates via pip

### 6.3 Custom Path for Testing

```python
from pathlib import Path
from home_secret_toml import HomeSecretToml

# Use a test secrets file
hs_test = HomeSecretToml(path=Path("tests/fixtures/test_secrets.toml"))
api_key = hs_test.v("github.accounts.personal.account_id")
```

### 6.4 Token-Based Configuration

```python
from home_secret_toml import hs

class MyConfig:
    github_token = hs.t("github.accounts.personal.users.dev.secrets.api_token.value")
    aws_access_key = hs.t("aws.accounts.prod.secrets.deploy.creds")

# Values are resolved only when accessed
config = MyConfig()
print(config.github_token.v)  # Resolves here
```

### 6.5 IDE Autocomplete with Generated Enum

```bash
hst gen-enum
```

```python
from home_secret_enum import Secret

# Full IDE autocomplete support
api_key = Secret.github__accounts__personal__users__dev__secrets__api_token__value.v
```

## 7. Error Handling

### 7.1 File Not Found

When the secrets file does not exist at the expected location:

```python
raise FileNotFoundError(f"Secret file not found at {path}")
```

### 7.2 Invalid Path Access

When accessing a path that does not exist in the data:

```python
raise KeyError(f"Key '{current_path}' not found in the provided data.")
```

The error message includes the partial path that was successfully traversed before failure.

### 7.3 File Already Exists (Enum Generation)

When generating enum file and it already exists:

```python
raise FileExistsError(f"{output_path} already exists. Use --overwrite to replace it.")
```

## 8. Security Considerations

### 8.1 File Permissions

The secrets file SHOULD have restricted permissions:
- Unix/Linux/macOS: `0600` (owner read/write only)
- Windows: Accessible only to the current user

### 8.2 Version Control

The following files MUST be added to `.gitignore`:
- `home_secret.toml` (the actual secrets file)
- `home_secret_enum.py` (generated enum may contain path hints)

### 8.3 Value Masking

The CLI `hst ls` command always masks secret values:
- Non-string values: `*`
- Short strings (≤8 chars): `***`
- Long strings (>8 chars): `ab***yz` (first 2 and last 2 chars)

### 8.4 Logging

The library SHALL NOT log secret values. Only paths (not values) may appear in error messages.

## 9. Comparison with JSON Format

| Aspect | JSON Format | TOML Format |
|--------|-------------|-------------|
| Structure | Nested objects | Flat key-value pairs |
| Context visibility | Must scroll/collapse to see context | Full context in every line |
| Comments | Not supported | Native support with `#` |
| Human editing | Error-prone (brackets, commas) | Straightforward |
| File size | Smaller (no key repetition) | Larger (full paths repeated) |
| Parsing complexity | Standard JSON | Standard TOML |
| Dependencies | `json` (stdlib) | `tomllib` (Python 3.11+ stdlib) |

## 10. Dependencies

**Runtime Dependencies:**
- Python 3.11+ (for `tomllib` standard library module)
- No external packages required

**Development Dependencies (optional):**
- `pytest` for testing
- `pytest-cov` for coverage

## 11. Module Structure

```
home_secret_toml/
├── __init__.py          # Package initialization, exports public API
├── api.py               # Public API exports
├── cli.py               # CLI entry point (calls main() from home_secret_toml.py)
├── paths.py             # Path constants
└── home_secret_toml.py  # Core implementation (self-contained, can be copied standalone)
```

## 12. Public API Summary

The following symbols are exported as the public API:

| Symbol | Type | Description |
|--------|------|-------------|
| `HomeSecretToml` | Class | Main interface for loading and accessing secrets |
| `Token` | Class | Lazy-loading reference to a secret value |
| `hs` | Instance | Pre-configured global HomeSecretToml instance |
| `gen_enum_code` | Function | Low-level function to generate Python enum code |
| `generate_enum` | Function | High-level function to generate enum file with error handling |
| `list_secrets` | Function | List all secrets with masked values |
| `mask_value` | Function | Mask a secret value for safe display |
| `walk` | Function | Traverse nested dict and yield leaf paths/values |