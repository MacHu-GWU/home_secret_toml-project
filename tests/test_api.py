# -*- coding: utf-8 -*-

from home_secret_toml import api


def test():
    _ = api
    _ = api.HomeSecretToml
    _ = api.Token
    _ = api.hs
    _ = api.gen_enum_code


if __name__ == "__main__":
    from home_secret_toml.tests import run_cov_test

    run_cov_test(
        __file__,
        "home_secret_toml.api",
        preview=False,
    )
