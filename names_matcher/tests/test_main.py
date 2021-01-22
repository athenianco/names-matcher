import sys
from tempfile import NamedTemporaryFile
from unittest.mock import patch

from names_matcher.__main__ import main


def test_main(capsys):
    with NamedTemporaryFile(mode="w+", prefix="test_names_matcher_") as f1:
        f1.write("""Vadim Markovtsev
Waren Long""")
        f1.flush()
        with NamedTemporaryFile(mode="w+", prefix="test_names_matcher_") as f2:
            f2.write("""Long Waren
vmarkovtsev|vadim
""")
            f2.flush()
            with patch.object(sys, "argv", ["", f1.name, f2.name]):
                main()
            assert capsys.readouterr().out == """vmarkovtsev|vadim
Long Waren
"""
