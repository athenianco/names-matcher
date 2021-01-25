import re
from typing import Iterable, Sequence, Set, Tuple, Union
import warnings

from lapjv import lapjv
from metaphone import doublemetaphone
import numpy as np
from unidecode import unidecode


class NamesMatcher:
    """
    Fuzzy names matching algorithm.

    Let's define an identity as a series of names belonging to the same person.

    1. Parse, normalize, and split names in each identity. The result is a set of strings for \
       each identity.
    2. Define the similarity between identities as the Jaccard similarity between their sets of \
       strings.
    3. Construct the distance matrix between identities in two specified lists.
    4. Solve the Linear Assignment Problem (LAP) on that matrix.

    We use metaphones in the normalization step to reduce the influence of different spelling and
    typos. We use lapjv to solve the LAP, so our solution scales to ~1000-s of identities.
    If you have a bigger problem size, you should use MinHashes (e.g. http://ekzhu.com/datasketch/)
    over the identity sets produced by `reap_identity()`.

    Example:
    >>> NamesMatcher()([["Vadim Markovtsev", "vmarkovtsev"], ["Long, Waren", "warenlg"]], \
                        [["Warren"], ["VMarkovtsev"], ["Eiso Kant"]])
    (array([1, 0], dtype=int32), array([0.75      , 0.57142857]))
    """

    initials_re = re.compile(r"(?<=[a-z])(?=[A-Z])|([A-Z])(?=[A-Z]+[a-z])")
    nonalphanumeric_re = re.compile(r"[^A-Za-z0-9 ]+")
    whitespace_re = re.compile(r" +")
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
        self._stop_words_re = re.compile("|".join(stop_words))

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
        parts1, parts2 = ([self.reap_identity(n) for n in names] for names in (names1, names2))
        return self.match_parts(parts1, parts2)

    def match_parts(self,
                    parts1: Sequence[Set[str]],
                    parts2: Sequence[Set[str]],
                    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Match parsed, normalized, split identities. You shouldn't use this function unless you \
        know what you are doing.

        `parts1` and `parts2` do not have to be the same length.
        Each identity is one or several parts.
        :return: numpy array with mapping indexes, so that `parts2[return] ~= parts1`. \
                 If there is no match found, the index is negative. \
                 numpy array with mapping confidences from 0 to 1.
        """
        distances = np.ones(((offset := len(parts1)) + len(parts2),) * 2)
        if distances.shape[0] > 10000:
            warnings.warn("Matching more than 10,000 names in sum is likely a heavy LAP and will "
                          "take much time.", ResourceWarning)
        distance = self.distance
        for y, part1 in enumerate(parts1):
            for x, part2 in enumerate(parts2):
                distances[y, offset + x] = distances[offset + x, y] = distance(part1, part2)
        r"""
        Our distance matrix:
                        <offset>
                  ---------|-----------------
                 | 1 1 1 1 |    distances    |  \
                 | 1 1 1 1 |     1 -> 2      |    parts1
                 | 1 1 1 1 |                 |  /
        <offset> |---------|-----------------|
                 | distan- | 1 1 1 1 1 1 1 1 |  \
                 | ces     | 1 1 1 1 1 1 1 1 |
                 | 2 -> 1  | 1 1 1 1 1 1 1 1 |    parts2
                 |         | 1 1 1 1 1 1 1 1 |
                 |         | 1 1 1 1 1 1 1 1 |  /
                  ---------|-----------------
                  \       / \               /
                   parts1        parts2
        """
        row_ind, _, _ = lapjv(distances)
        assignments = row_ind[:offset] - offset
        confidences = 1 - distances[tuple(np.vstack([np.arange(offset), row_ind[:offset]]))]
        # there can be matches (1) -> (1) in case everything in (2) is at distance 1
        confidences[assignments < 0] = 1
        assignments[assignments < 0] = -1
        return assignments, confidences

    @staticmethod
    def distance(parts1: Set[str], parts2: Set[str]) -> float:
        """Jaccard distance between two sets."""
        if not parts1 and not parts2:
            return 1
        return 1 - len(parts1.intersection(parts2)) / len(parts1.union(parts2))

    def reap_identity(self, names: Iterable[str]) -> Set[str]:
        """Parse, normalize, and split names to a set of characteristic strings."""
        initials_re = self.initials_re
        nonalphanumeric_re = self.nonalphanumeric_re
        whitespace_re = self.whitespace_re
        stop_words_re = self._stop_words_re

        parts = set()
        for name in names:
            normal = unidecode(name)
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
                    # this cycle always iterates twice (aka "double")
                    for metaphone in doublemetaphone(part):
                        if metaphone:
                            parts.add(metaphone)
                            if len(metaphone) > 1:
                                # possible abbreviation
                                parts.add(metaphone[0])

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
                            # both work wrong when the metaphone ate a double consonant
                            if part2.startswith(part1):
                                removed.append(part2)
                                added.append(part2[len(part1):])
                                added.append(part2[len(part1)])
                            elif part2.endswith(part1):
                                removed.append(part2)
                                added.append(part2[:-len(part1)])
                                # abbreviation is already included
            for part in removed:
                try:
                    parts.remove(part)
                except KeyError:
                    continue
            parts.update(added)
            if not removed and not added:
                break
        return parts
