import re
from typing import Iterable, Sequence, Set, Tuple, Union
import warnings

from lapjv import lapjv
import numpy as np
try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable):
        """No-op tqdm shim."""
        return iterable
from rapidfuzz import fuzz
from unidecode import unidecode


NormalizedIdentity = Tuple[Set[str], str]


class NamesMatcher:
    """
    Fuzzy names matching algorithm.

    Let's define an identity as a series of names belonging to the same person.

    1. Parse, normalize, and split names in each identity. The result is a set of strings per each.
    2. Define the similarity between identities as `max(ratio, token_set_ratio)`, where `ratio` \
       and `token_set_ratio` are inspired by string comparison functions from FuzzyWuzzy.
    3. Construct the distance matrix between identities in two specified lists.
    4. Solve the Linear Assignment Problem (LAP) on that matrix.

    Our LAP's solution scales up to ~1000-s of identities.

    Example:
    >>> NamesMatcher()([["Vadim Markovtsev", "vmarkovtsev"], ["Long, Waren", "warenlg"]], \
                        [["Warren"], ["VMarkovtsev"], ["Eiso Kant"]])
    (array([1, 0], dtype=int32), array([1.        , 0.58823529]))
    """

    initials_re = re.compile(r"(?<=[a-z])(?=[A-Z])|([A-Z])(?=[A-Z]+[a-z])")
    nonalphanumeric_re = re.compile(r"[^A-Za-z0-9 ]+")
    whitespace_re = re.compile(r" +")
    repetitions_re = re.compile(r"(.{2,})(.*)\1+")
    stop_words = {
        "github": ["rebase",
                   "rebasing",
                   "pr",
                   "action",
                   "script",
                   "release",
                   "unknown",
                   "root",
                   "admin",
                   "localhost",
                   "refresher",
                   "bump",
                   "lint",
                   "update",
                   "and",
                   ],
    }

    def __init__(self,
                 stop_words: Union[str, Iterable[str]] = "github",
                 ):
        """
        Initialize a new instance of NamesMatcher class.

        :param stop_words: Ignore parsed name parts that start with any string from this list. \
                           You can use regular expression syntax.
        """
        if isinstance(stop_words, str):
            stop_words = self.stop_words[stop_words]
        self._stop_words_re = re.compile("|".join(stop_words) if stop_words else "(?!.*)")

    def __call__(self,
                 names1: Iterable[Iterable[str]],
                 names2: Iterable[Iterable[str]],
                 ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Match people names from `names1` to `names2`.

        `names1` and `names2` do not have to be the same length.
        Each identity is one or several names.
        :return: numpy array with mapping indexes, so that `names2[return] ~= names1`. \
                 If there is no match found, the index is negative. \
                 numpy array with mapping confidences from 0 to 1.
        """
        return self.match_parts(
            *([self.reap_identity(n) for n in names] for names in (names1, names2)))

    def match_parts(self,
                    parts1: Sequence[NormalizedIdentity],
                    parts2: Sequence[NormalizedIdentity],
                    disable_progress: bool = False,
                    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Match parsed, normalized, split identities. You shouldn't use this function unless you \
        know what you are doing.

        `tokens1` and `tokens2` do not have to be the same length.
        Each identity is one or several parts.
        :param disable_progress: Value indicating whether to disable tqdm progress indication \
                                 for computing big distance matrices.
        :return: numpy array with mapping indexes, so that `tokens2[return] ~= tokens1`. \
                 If there is no match found, the index is negative. \
                 numpy array with mapping confidences from 0 to 1.
        """
        distances = np.ones(((offset := len(parts1)) + len(parts2),) * 2)
        distance = self.distance
        if not disable_progress and len(parts1) * len(parts2) >= 500000:
            parts1 = tqdm(parts1)
        for y, part1 in enumerate(parts1):
            for x, part2 in enumerate(parts2):
                distances[y, offset + x] = distances[offset + x, y] = distance(part1, part2)
        return self.solve_lap(distances, offset)

    @staticmethod
    def solve_lap(distances: np.ndarray, offset: int) -> Tuple[np.ndarray, np.ndarray]:
        r"""
        Solve the LAP on the given distance matrix. You shouldn't use this function unless you \
        know what you are doing.

        The distance matrix should be of this form:

                        <offset>
                  ---------|-----------------
                 | 1 1 1 1 |    distances    |  \
                 | 1 1 1 1 |     1 -> 2      |    tokens1
                 | 1 1 1 1 |                 |  /
        <offset> |---------|-----------------|
                 | distan- | 1 1 1 1 1 1 1 1 |  \
                 | ces     | 1 1 1 1 1 1 1 1 |
                 | 2 -> 1  | 1 1 1 1 1 1 1 1 |    tokens2
                 |         | 1 1 1 1 1 1 1 1 |
                 |         | 1 1 1 1 1 1 1 1 |  /
                  ---------|-----------------
                  \       / \               /
                   tokens1        tokens2
        """  # noqa: D400, D205
        if distances.shape[0] >= 10000:
            warnings.warn("Matching %d x %d names is likely a heavy LAP and will take much time." %
                          (offset, len(distances) - offset), ResourceWarning)
        row_ind, _, _ = lapjv(distances)
        assignments = row_ind[:offset] - offset
        confidences = 1 - distances[tuple(np.vstack([np.arange(offset), row_ind[:offset]]))]
        # there can be matches (1) -> (1) in case everything in (2) is at distance 1
        confidences[assignments < 0] = 1
        assignments[assignments < 0] = -1
        return assignments, confidences

    @staticmethod
    def distance(id1: NormalizedIdentity, id2: NormalizedIdentity) -> float:
        """
        FuzzyWuzzy distance between two identities.

        We take the max of `token_set_ratio()` and `ratio()`.
        """  # noqa: D403
        tokens1, concat1 = id1
        tokens2, concat2 = id2
        if not tokens1 or not tokens2:
            return 1
        assert concat1
        assert concat2

        # the following is a copy-paste from FuzzyWuzzy's token_set_ratio()
        intersection = tokens1.intersection(tokens2)
        diff1to2 = tokens1.difference(tokens2)
        diff2to1 = tokens2.difference(tokens1)

        sorted_sect = " ".join(sorted(intersection))
        sorted_1to2 = " ".join(sorted(diff1to2))
        sorted_2to1 = " ".join(sorted(diff2to1))

        combined_1to2 = sorted_sect + " " + sorted_1to2
        combined_2to1 = sorted_sect + " " + sorted_2to1

        sorted_sect = sorted_sect.strip()
        combined_1to2 = combined_1to2.strip()
        combined_2to1 = combined_2to1.strip()

        # Pick the best our of 4: the normalized concatentation and the 3 set variants
        pairwise = [fuzz.ratio(*pair) / 100 for pair in (
            (concat1, concat2),
            (sorted_sect, combined_1to2),
            (sorted_sect, combined_2to1),
            (combined_1to2, combined_2to1),
        )]

        return 1 - max(pairwise)

    def reap_identity(self, names: Iterable[str]) -> NormalizedIdentity:
        """
        Parse, normalize, and split names to a set of characteristic strings.

        :return: 1. Set of normalized name atoms. \
                 2. Normalized names concatenation.
        """
        initials_re = self.initials_re
        nonalphanumeric_re = self.nonalphanumeric_re
        whitespace_re = self.whitespace_re
        stop_words_re = self._stop_words_re

        parts = set()
        amalgamation = []
        for name in names:
            normal = unidecode(name)
            concat = ""
            for variant in initials_re.split(normal):
                # break by lower -> UPPER case change and by UPPER -> UPPER+ -> lower
                # examples:
                # VadimMarkovtsev -> Vadim Markovtsev
                # VMarkovtsev -> V Markovtsev
                if not variant:
                    continue
                variant = variant.lower()
                # replace all non-alpha and non-numeric chars with a whitespace
                variant = nonalphanumeric_re.sub(" ", variant)
                # collapse sequential whitespaces
                variant = whitespace_re.sub(" ", variant)
                variant = variant.strip()
                if not variant:
                    continue
                for part in variant.split(" "):
                    # if we start with a stop word, ignore
                    if stop_words_re.match(part):
                        continue
                    concat += part
                    parts.add(part)
            amalgamation.append(concat)
        amalgamation = "".join(sorted(amalgamation))
        amalgamation = self.repetitions_re.sub(r"\1\2", amalgamation)

        # remove compounds, split them by prefix and by suffix
        while True:
            removed = []
            added = []
            for part1 in parts:
                for part2 in parts:
                    if part1 != part2:
                        if (concat := (part1 + part2)) in parts:
                            removed.append(concat)
                        if len(part1) >= 2:
                            if part2.startswith(part1):
                                removed.append(part2)
                                added.append(part2[len(part1):])
                            elif part2.endswith(part1):
                                removed.append(part2)
                                added.append(part2[:-len(part1)])
            for part in removed:
                try:
                    parts.remove(part)
                except KeyError:
                    continue
            parts.update(added)
            if not removed and not added:
                break
        return parts, amalgamation
