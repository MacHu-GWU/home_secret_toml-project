# -*- coding: utf-8 -*-

"""
CLI entry point module for home_secret_toml.

This module provides the entry point for the ``hst`` command when installed via pip.
It simply imports and calls the main() function from home_secret_toml.
"""

from .home_secret_toml import main


def run() -> None:
    """
    Entry point function for the hst CLI command.

    This function is called when running ``hst`` from the command line
    after installing the package via pip.
    """
    main()


if __name__ == "__main__":
    run()
