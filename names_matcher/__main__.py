import sys

from names_matcher.algorithm import NamesMatcher


def main():
    """
    Given two text files with one identity per line, output the matches from \
    the first to the second.

    The names are expected to be joined by "|". The result is printed to stdout, lines from
    the second file in the sequence of the first file.
    """
    if len(sys.argv) != 3:
        print("Usage: path/to/file/1 path/to/file/2", file=sys.stderr)
        return 1
    names = [None] * 2
    for arg in (1, 2):
        with open(sys.argv[arg]) as fin:
            names[arg - 1] = [line.split("|") for line in fin]
    for match in NamesMatcher()(*names)[0]:
        if match < 0:
            print()
        else:
            sys.stdout.write("|".join(names[1][match]))


if __name__ == "__main__":
    sys.exit(main())
