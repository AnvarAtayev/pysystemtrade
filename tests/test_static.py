import subprocess
import os
import unittest

THIS_DIR = os.path.dirname(__file__)
MOD_DIR = os.path.join(THIS_DIR, "..")


@unittest.SkipTest
def test_ruff_lint():
    retcode = subprocess.call(
        [
            "ruff",
            "check",
            MOD_DIR,
        ]
    )
    assert retcode == 0
