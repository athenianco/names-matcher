import os
import platform
import sys
from tempfile import NamedTemporaryFile
from unittest.mock import patch

from names_matcher.__main__ import main


def test_main(capsys):
    is_windows = platform.system() == "Windows"
    with NamedTemporaryFile(mode="w+", prefix="test_names_matcher_",
                            delete=not is_windows) as f1:
        f1.write("""Vadim Markovtsev
Waren Long""")
        f1.flush()
        with NamedTemporaryFile(mode="w+", prefix="test_names_matcher_",
                                delete=not is_windows) as f2:
            f2.write("""Long Waren
vmarkovtsev|vadim
""")
            f2.flush()
            if is_windows:
                f1.close()
                f2.close()
            with patch.object(sys, "argv", ["", f1.name, f2.name]):
                try:
                    main()
                finally:
                    if is_windows:
                        os.remove(f1.name)
                        os.remove(f2.name)
            assert capsys.readouterr().out == """vmarkovtsev|vadim
Long Waren
"""
