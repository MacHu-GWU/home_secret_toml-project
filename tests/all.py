# -*- coding: utf-8 -*-

if __name__ == "__main__":
    from home_secret_toml.tests import run_cov_test

    run_cov_test(
        __file__,
        "home_secret_toml",
        is_folder=True,
        preview=False,
    )
