.. _release_history:

Release and Version History
==============================================================================


x.y.z (Backlog)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


0.2.1 (2025-12-12)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Added ``hst get`` command to retrieve secret values by key. This command outputs the secret value to stdout, making it easy to capture in shell variables (e.g., ``export TOKEN=$(hst get github.token)``). Supports the following options:

    - Positional key argument: ``hst get github.accounts.personal.token``
    - ``--key`` option: ``hst get --key github.accounts.personal.token``
    - ``-c / --clipboard``: Copy value to clipboard instead of printing
    - ``-n / --no-newline``: Omit trailing newline for pipe-friendly output
    - ``--path``: Specify custom TOML file path


0.1.2 (2025-12-10)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Added Python 3.10 and 3.14 support, expanding compatibility across more Python versions.
- Added ``tomli`` as a dependency for Python <3.11 to provide TOML parsing support for older Python versions that don't have built-in ``tomllib``.

**Miscellaneous**

- Updated CI workflow to test against full OS and Python version matrix.


0.1.1 (1970-01-01)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- First release
