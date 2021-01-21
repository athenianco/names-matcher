from importlib.machinery import SourceFileLoader
from pathlib import Path

from setuptools import find_packages, setup

project_root = Path(__file__).parent
code_root = project_root / "names_matcher"
metadata = SourceFileLoader("metadata", str(code_root / "metadata.py")).load_module()

with open(project_root / "README.md", encoding="utf-8") as f:
    long_description = f.read()


setup(
    name=metadata.__package__.replace(".", "-"),
    description=metadata.__description__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    version=metadata.__version__,
    license="Apache-2.0",
    author="Athenian",
    author_email="vadim@athenian.co",
    url="https://github.com/athenian/names-matcher",
    packages=find_packages(exclude=["tests"]),
    keywords=["fuzzy matching"],
    install_requires=["numpy>=1.0.0",
                      "lapjv>=1.3.10,<2.0",
                      "metaphone>=0.6,<2.0",
                      "unidecode>=1.0.0,<2.0",
                      ],
    tests_require=[],
    package_data={
        "": ["README.md"],
        "names_matcher": ["../requirements.txt"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License",
    ],
)
