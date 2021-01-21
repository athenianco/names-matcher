# Contributing Guidelines

names-matcher is [Apache-2.0 licensed](LICENSE) and accepts
contributions via GitHub pull requests.  This document outlines some
conventions on the development workflow, commit message formatting, contact points,
and other resources to make it easier to get your contribution accepted.

## Certificate of Origin

By contributing to this project you agree to the [Developer Certificate of
Origin (DCO)](DCO). This document was created by the Linux Kernel community and is a
simple statement that you, as a contributor, have the legal right to make the
contribution.

In order to show your agreement with the DCO you should include at the end of commit message,
the following line: `Signed-off-by: John Doe <john.doe@example.com>`, using your real name.

This can be done easily using the [`-s`](https://github.com/git/git/blob/b2c150d3aa82f6583b9aadfecc5f8fa1c74aca09/Documentation/git-commit.txt#L154-L161) flag on the `git commit`.


## Support Channels

The official support channels, for both users and contributors, are:

- GitHub [issues](https://github.com/athenianco/names-matcher/issues)*

*Before opening a new issue or submitting a new pull request, it's helpful to
search around - it's likely that another user has already reported the
issue you're facing, or it's a known issue that we're already aware of.


## How to Contribute

Pull Requests (PRs) are the main and exclusive way to contribute to the official project.
In order for a PR to be accepted it needs to pass a list of requirements:

- The commit messages must be formatted as specified below.
- The CI checks pass. This includes both the style checks (`make check`) and the tests.
- Code Coverage does not decrease.
- Python code is formatted according to [![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/) and the [flake8](https://flake8.pycqa.org/en/latest/) configuration.
- If the PR is a bug fix, it has to include a new unit test that fails before the patch is merged.
- If the PR is a new feature, it has to come with a suite of unit tests of the new functionality.
- In any case, all the PRs have to pass the personal evaluation of at least one of the [maintainers](MAINTAINERS.md).


### Format of the commit message

The commit summary must start with a capital letter and with a verb in present tense. No dot in the end.

```
Add a feature
Remove unused code
Fix a bug
```

Every commit details should describe what was changed, under which context and, if applicable, the GitHub issue it relates to.
