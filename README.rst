
.. image:: https://readthedocs.org/projects/home-secret-toml/badge/?version=latest
    :target: https://home-secret-toml.readthedocs.io/en/latest/
    :alt: Documentation Status

.. image:: https://github.com/MacHu-GWU/home_secret_toml-project/actions/workflows/main.yml/badge.svg
    :target: https://github.com/MacHu-GWU/home_secret_toml-project/actions?query=workflow:CI

.. image:: https://codecov.io/gh/MacHu-GWU/home_secret_toml-project/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/MacHu-GWU/home_secret_toml-project

.. image:: https://img.shields.io/pypi/v/home-secret-toml.svg
    :target: https://pypi.python.org/pypi/home-secret-toml

.. image:: https://img.shields.io/pypi/l/home-secret-toml.svg
    :target: https://pypi.python.org/pypi/home-secret-toml

.. image:: https://img.shields.io/pypi/pyversions/home-secret-toml.svg
    :target: https://pypi.python.org/pypi/home-secret-toml

.. image:: https://img.shields.io/badge/✍️_Release_History!--None.svg?style=social&logo=github
    :target: https://github.com/MacHu-GWU/home_secret_toml-project/blob/main/release-history.rst

.. image:: https://img.shields.io/badge/⭐_Star_me_on_GitHub!--None.svg?style=social&logo=github
    :target: https://github.com/MacHu-GWU/home_secret_toml-project

------

.. image:: https://img.shields.io/badge/Link-API-blue.svg
    :target: https://home-secret-toml.readthedocs.io/en/latest/py-modindex.html

.. image:: https://img.shields.io/badge/Link-Install-blue.svg
    :target: `install`_

.. image:: https://img.shields.io/badge/Link-GitHub-blue.svg
    :target: https://github.com/MacHu-GWU/home_secret_toml-project

.. image:: https://img.shields.io/badge/Link-Submit_Issue-blue.svg
    :target: https://github.com/MacHu-GWU/home_secret_toml-project/issues

.. image:: https://img.shields.io/badge/Link-Request_Feature-blue.svg
    :target: https://github.com/MacHu-GWU/home_secret_toml-project/issues

.. image:: https://img.shields.io/badge/Link-Download-blue.svg
    :target: https://pypi.org/pypi/home-secret-toml#files


Welcome to ``home_secret_toml`` Documentation
==============================================================================
.. image:: https://home-secret-toml.readthedocs.io/en/latest/_static/home_secret_toml-logo.png
    :target: https://home-secret-toml.readthedocs.io/en/latest/

Modern software development presents an increasingly complex credential management challenge. As cloud services proliferate and microservice architectures become standard, developers face exponential growth in sensitive information requiring secure storage and convenient access—API keys, database credentials, authentication tokens, and service endpoints.

This complexity creates a fundamental tension: developers need immediate access to credentials during development while maintaining rigorous security standards. Traditional approaches, from hardcoded secrets to scattered environment variables, fail to address the sophisticated demands of contemporary multi-platform, multi-account development workflows.

The consequences of inadequate credential management extend beyond inconvenience. Security breaches, development inefficiencies, and maintenance nightmares plague teams using fragmented approaches. What developers need is a systematic solution that unifies security, accessibility, and scalability into a coherent framework.

HOME Secret TOML emerges as a response to these challenges—a comprehensive local credential management system built on structured `TOML <https://toml.io/en/>`_ configuration and intelligent Python integration. Unlike nested JSON structures, TOML's **flat key-value format** provides immediate context visibility in every line, making secrets easy to navigate and edit. This approach transforms credential management from a necessary evil into a streamlined development asset.

**Key Features**

- **Flat Key Structure**: Every secret is a single line with full path context—no nested brackets to manage
- **Comment Support**: Native ``#`` comments for documentation directly in the secrets file
- **Zero Dependencies**: Uses only Python 3.11+ standard library (``tomllib``)
- **Dual Usage**: Copy single file to your project OR ``pip install`` as a package
- **CLI Tool**: ``hst ls`` to list secrets, ``hst gen-enum`` to generate IDE autocomplete code
- **IDE Support**: Generated enum classes provide full autocomplete and type checking

**Quick Links**

- `Comprehensive Document <https://github.com/MacHu-GWU/home_secret_toml-project/blob/main/home-secret-toml-a-unified-approach-to-local-development-credential-management.md>`_
- `Home secret TOML core source code <https://github.com/MacHu-GWU/home_secret_toml-project/blob/main/home_secret_toml/home_secret_toml.py>`_
- `Sample home_secret.toml file <https://github.com/MacHu-GWU/home_secret_toml-project/blob/main/home_secret_toml/home_secret.toml>`_


.. _install:

Install
------------------------------------------------------------------------------

``home_secret_toml`` is released on PyPI, so all you need is to:

.. code-block:: console

    $ pip install home-secret-toml

To upgrade to latest version:

.. code-block:: console

    $ pip install --upgrade home-secret-toml


Quick Start
------------------------------------------------------------------------------

1. Create ``~/home_secret.toml`` with your secrets:

.. code-block:: toml

    # GitHub credentials
    github.accounts.personal.account_id = "myuser"
    github.accounts.personal.users.dev.secrets.api_token.value = "ghp_xxxxxxxxxxxx"

    # AWS credentials
    aws.accounts.prod.secrets.deploy.creds = { access_key = "AKIA...", secret_key = "xxxx" }

2. Access secrets in Python:

.. code-block:: python

    from home_secret_toml import hs

    # Direct value access
    api_key = hs.v("github.accounts.personal.users.dev.secrets.api_token.value")

    # Token-based (lazy) access
    token = hs.t("github.accounts.personal.users.dev.secrets.api_token.value")
    api_key = token.v  # Resolved when accessed

3. Use CLI to explore and generate code:

.. code-block:: console

    # List all secrets (values are masked)
    $ hst ls
    github.accounts.personal.account_id = "***"
    github.accounts.personal.users.dev.secrets.api_token.value = "gh***xx"

    # Filter secrets
    $ hst ls --query "github personal"

    # Generate enum file for IDE autocomplete
    $ hst gen-enum


Single-File Usage (No pip install)
------------------------------------------------------------------------------

For projects where you want zero dependencies, simply copy ``home_secret_toml.py`` to your project:

.. code-block:: python

    # Copy the file and import directly
    from home_secret_toml import hs

    api_key = hs.v("github.accounts.personal.users.dev.secrets.api_token.value")

Requirements: Python 3.11+ (for built-in ``tomllib`` module)
