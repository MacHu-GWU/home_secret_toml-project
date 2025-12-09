# HOME Secret TOML Specification

## 1. Overview

HOME Secret TOML is a local credential management system that stores sensitive development credentials in a structured TOML configuration file. It provides a flat, human-readable format for organizing secrets across multiple service providers, accounts, and users, with Python integration for secure programmatic access.

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

## 3. File Format Specification

### 3.1 File Location

The primary secrets file MUST be located at:

```
$HOME/home_secret.toml
```

Where `$HOME` represents the user's home directory (e.g., `/Users/username` on macOS, `/home/username` on Linux, `C:\Users\username` on Windows).

### 3.2 Key Format

Keys follow a dot-separated path notation with the following constraints:

- Keys contain only lowercase letters, numbers, and underscores
- Path segments are separated by dots (`.`)
- **No nested tables allowed** - all keys must be at the root level of the TOML file
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

The `HomeSecretToml` class is the primary interface for loading and accessing secrets from the TOML file.

#### 4.1.1 Constructor

```python
class HomeSecretToml:
    def __init__(self, path: Optional[Path] = None):
        """
        Initialize the HomeSecretToml instance.

        Args:
            path: Optional custom path to the TOML file.
                  Defaults to $HOME/home_secret.toml
        """
```

#### 4.1.2 Properties

**`data`** (read-only)

```python
@property
def data(self) -> dict[str, Any]:
    """
    Load and cache the secret data from the home_secret.toml file.

    Returns:
        A dictionary representation of the TOML file where dot-separated
        keys are preserved as flattened string keys.

    Raises:
        FileNotFoundError: If the secrets file does not exist
        toml.TomlDecodeError: If the TOML file is malformed

    Note:
        This property is lazy-loaded and cached. The file is only read
        from disk on first access. The returned dictionary MUST NOT be
        modified by the caller.
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
        V stands for "Value". Results are cached for performance.
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
        T stands for "Token". Useful for dependency injection and
        configuration objects where value resolution should be deferred.
    """
```

### 4.2 Token Class

The `Token` class represents a lazy reference to a secret value.

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

The module SHALL provide a pre-configured global instance for convenience:

```python
hs = HomeSecretToml()
```

This allows simple usage patterns:

```python
from home_secret_toml import hs

api_key = hs.v("github.accounts.personal.users.dev.secrets.api_token.value")
```

### 4.4 Enum Code Generation

The library SHALL provide a function to generate a Python module containing enumerated access to all secrets.

**`gen_enum_code(output_path: Optional[Path] = None) -> None`**

```python
def gen_enum_code(output_path: Optional[Path] = None) -> None:
    """
    Generate a Python module with enumerated secret path constants.

    This function creates a Secret class where each secret path becomes
    a class attribute, enabling IDE autocomplete and static analysis.

    Args:
        output_path: Path to write the generated file.
                     Defaults to ./home_secret_enum.py

    Generated File Structure:
        - A Secret class with attributes for each secret path
        - Attribute names are derived from paths by:
          1. Replacing dots with double underscores
          2. Using only valid Python identifier characters
        - Each attribute is a Token object for lazy value resolution
        - A _validate_secret() function to verify all paths are valid
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
2. The full path is preserved (unlike the JSON version which removes the `providers.` prefix, TOML version keeps the full path since there is no `providers` wrapper)

#### 4.4.3 Filtering Rules

The following entries SHALL be excluded from the generated enum:

1. Entries where the value equals the placeholder string `"..."`
2. Entries where the key ends with `.description` (metadata only)

## 5. File Synchronization Behavior

### 5.1 Development Workflow Support

The library MAY support automatic synchronization from a project-local file to the home directory location:

```
${PROJECT_DIR}/home_secret.toml  →  $HOME/home_secret.toml
```

This enables developers to:
1. Keep a project-specific secrets file (excluded from version control)
2. Have it automatically copied to the runtime location

### 5.2 Synchronization Configuration

The synchronization behavior SHALL be controllable:

```python
# Module-level configuration
IS_SYNC = True  # Enable/disable synchronization

# Path configuration
p_here_secret = Path("home_secret.toml").absolute()  # Source location
p_home_secret = Path.home() / "home_secret.toml"     # Runtime location
```

## 6. Error Handling

### 6.1 File Not Found

When the secrets file does not exist at the expected location:

```python
raise FileNotFoundError(f"Secret file not found at {path}")
```

### 6.2 Invalid Path Access

When accessing a path that does not exist in the data:

```python
raise KeyError(f"Key '{path}' not found in the provided data.")
```

The error message SHALL include the full path that was attempted.

### 6.3 TOML Parse Errors

When the TOML file contains syntax errors, the standard `toml.TomlDecodeError` (or equivalent from the TOML parsing library) SHALL be raised with line number information.

## 7. Security Considerations

### 7.1 File Permissions

The secrets file SHOULD have restricted permissions:
- Unix/Linux/macOS: `0600` (owner read/write only)
- Windows: Accessible only to the current user

### 7.2 Version Control

The following files MUST be added to `.gitignore`:
- `home_secret.toml` (the actual secrets file)
- `home_secret_enum.py` (generated enum may contain path hints)

### 7.3 Logging

The library SHALL NOT log secret values. If logging is implemented, only paths (not values) may be logged.

## 8. Comparison with JSON Format

| Aspect | JSON Format | TOML Format |
|--------|-------------|-------------|
| Structure | Nested objects | Flat key-value pairs |
| Context visibility | Must scroll/collapse to see context | Full context in every line |
| Comments | Not supported | Native support with `#` |
| Human editing | Error-prone (brackets, commas) | Straightforward |
| File size | Smaller (no key repetition) | Larger (full paths repeated) |
| Parsing complexity | Standard JSON | Standard TOML |

## 9. Dependencies

The library SHALL depend on:
- Python 3.9+ (for modern type hints)
- A TOML parsing library (e.g., `tomllib` from Python 3.11+ stdlib, or `tomli` for earlier versions)

## 10. Module Structure

```
home_secret_toml/
├── __init__.py          # Package initialization, exports public API
├── api.py               # Public API exports
└── home_secret_toml.py  # Core implementation
```

## 11. Public API Summary

The following symbols SHALL be exported as the public API:

| Symbol | Type | Description |
|--------|------|-------------|
| `HomeSecretToml` | Class | Main interface for loading and accessing secrets |
| `Token` | Class | Lazy-loading reference to a secret value |
| `hs` | Instance | Pre-configured global HomeSecretToml instance |
| `gen_enum_code` | Function | Generate Python enum code from current secrets |