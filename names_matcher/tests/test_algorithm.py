import pytest

from names_matcher.algorithm import NamesMatcher


def test_docstring():
    assignments = NamesMatcher()([["Vadim Markovtsev", "vmarkovtsev"], ["Long, Waren", "warenlg"]],
                                 [["Warren"], ["VMarkovtsev"], "Eiso Kant"])
    assert assignments[0].tolist() == [1, 0]
    assert assignments[1].tolist() == [0.75, 0.5714285714285714]


@pytest.mark.parametrize("names, result", [
    [[], set()],
    [["VMarkovtsev", "vmarkovtsev"], {"M", "MRKFTSF", "F"}],
    [["markovtsev", "ricardomarkovtsev"], {"R", "M", "RKRT", "MRKFTSF"}],
    [["ricard", "ricardomarkovtsev"], {"R", "M", "RKRT", "MRKFTSF"}],
    [["Vadim_MARKOVTSEV (Rebase PR)"], {"F", "M", "FTM", "MRKFTSF"}],
    [["MarkõvtsevVádim"], {"F", "M", "FTM", "MRKFTSF"}],
])
def test_reap_idenity(names, result):
    assert NamesMatcher().reap_identity(names) == result, names


@pytest.mark.parametrize("names1, names2, result", [
    [{"a"}, {"a"}, 0],
    [set(), set(), 1],
    [set(), {"a"}, 1],
    [{"a", "b"}, {"a", "c"}, 2 / 3],
])
def test_distance(names1, names2, result):
    assert NamesMatcher.distance(names1, names2) == pytest.approx(result)


def test_warning():
    with pytest.warns(ResourceWarning):
        NamesMatcher().match_parts(*([[{str(i)} for i in range(5001)]] * 2))
