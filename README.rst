
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

HOME Secret emerges as a response to these challenges—a comprehensive local credential management system built on structured `TOML <https://toml.io/en/>`_ configuration and intelligent Python integration. This approach transforms credential management from a necessary evil into a streamlined development asset.


.. _install:

Install
------------------------------------------------------------------------------

``home_secret_toml`` is released on PyPI, so all you need is to:

.. code-block:: console

    $ pip install home-secret-toml

To upgrade to latest version:

.. code-block:: console

    $ pip install --upgrade home-secret-toml
