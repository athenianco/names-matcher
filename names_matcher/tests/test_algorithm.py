from typing import Iterable

import numpy as np
import pytest

from names_matcher.algorithm import NamesMatcher


def test_docstring():
    assignments = NamesMatcher()([["Vadim Markovtsev", "vmarkovtsev"], ["Long, Waren", "warenlg"]],
                                 [["Warren"], ["VMarkovtsev"], ["Eiso Kant"]])
    assert assignments[0].tolist() == [1, 0]
    assert assignments[1].tolist() == [1, 0.5882352941176471]


@pytest.mark.parametrize("names, result", [
    [[], (set(), "")],
    [["VMarkovtsev", "vmarkovtsev"], ({"v", "markovtsev"}, "vmarkovtsev")],
    [["markovtsev", "ricardomarkovtsev"], ({"ricardo", "markovtsev"}, "markovtsevricardo")],
    [["ricard", "ricardomarkovtsev"], ({"ricard", "omarkovtsev"}, "ricardomarkovtsev")],
    [["Vadim_MARKOVTSEV (Rebase PR)"], ({"vadim", "markovtsev"}, "vadimmarkovtsev")],
    [["MarkõvtsevVádim"], ({"vadim", "markovtsev"}, "markovtsevvadim")],
])
def test_reap_idenity(names: Iterable[str], result):
    assert NamesMatcher().reap_identity(names) == result, names


@pytest.mark.parametrize("names1, names2, result", [
    [({"a"}, "a"), ({"a"}, "a"), 0],
    [(set(), ""), (set(), ""), 1],
    [(set(), ""), ({"a"}, ""), 1],
    [({"a", "b"}, "ba"), ({"a", "c"}, "ca"), 1 / 3],
])
def test_distance(names1, names2, result):
    assert NamesMatcher.distance(names1, names2) == pytest.approx(result)


def test_progress_on(capsys):
    NamesMatcher().match_parts(*([[({"%04d" % i}, "%04d" % i) for i in range(1000)]] * 2))
    assert capsys.readouterr().err


def test_progress_off(capsys):
    NamesMatcher().match_parts(*([[({"%04d" % i}, "%04d" % i) for i in range(1000)]] * 2),
                               disable_progress=True)
    assert not capsys.readouterr().err


def test_warning():
    with pytest.warns(ResourceWarning):
        matrix = 1 - np.flip(np.eye(10000, dtype=np.float32), axis=0)
        NamesMatcher().solve_lap(matrix, len(matrix) // 2)
