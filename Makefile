current_dir = $(shell pwd)

PROJECT = names_matcher

.POSIX:
check:
	!(grep -R /tmp ${PROJECT}/tests)
	flake8

.PHONY: test
test:
	find -name "*.pyc" -delete
	pytest --cov-report=xml --cov=names_matcher -s -o log_cli=true -o log_cli_level=info -n 2

.PHONY: package
package:
	python setup.py --version
	python setup.py bdist_wheel sdist --format=gztar
	twine check dist/*

