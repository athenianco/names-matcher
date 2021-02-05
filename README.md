# names-matcher
[![Build Status](https://github.com/athenianco/names-matcher/workflows/Push/badge.svg?branch=master)](https://github.com/athenianco/names-matcher/actions)
[![Code coverage](https://codecov.io/github/athenianco/names-matcher/coverage.svg)](https://codecov.io/github/athenianco/names-matcher)
[![PyPI package](https://badgen.net/pypi/v/names-matcher)](https://pypi.org/project/names-matcher/)

Fuzzily biject people's names between two lists.

Let's define an identity as a series of names belonging to the same person. The algorithm is:

1. Parse, normalize, and split names in each identity. The result is a set of strings per each.
2. Define the similarity between identities as `max(ratio, token_set_ratio)`, where `ratio` \
   and `token_set_ratio` are inspired by string comparison functions from FuzzyWuzzy.
3. Construct the distance matrix between identities in two specified lists.
4. Solve the Linear Assignment Problem (LAP) on that matrix.

Our LAP's solution scales up to ~1000-s of identities.

Example:
```
>>> from names_matcher import NamesMatcher
>>> NamesMatcher()([["Vadim Markovtsev", "vmarkovtsev"], ["Long, Waren", "warenlg"]], \
                    [["Warren"], ["VMarkovtsev"], ["Eiso Kant"]])
(array([1, 0], dtype=int32), array([0.75      , 0.57142857]))
```
The first resulting tuple element is the mapping indexes: of same length as the first sequence,
with indexes in the second sequence. The second element is the corresponding confidence values
from 0 to 1.

### Installation

```
pip3 install names-matcher
```

### Command line interface

Given one identity per line in two files, print the matches to standard output:

```
python3 -m names_matcher path/to/file/1 path/to/file/2
```

Each identity is several names merged with `|`, for example:

```
Vadim Markovtsev|vmarkovtsev|vadim
```

### Contributing

Contributions are very welcome and desired! Please follow the [code of conduct](CODE_OF_CONDUCT.md) and read the [contribution guidelines](CONTRIBUTING.md).

### License

Apache-2.0, see [LICENSE](LICENSE).
