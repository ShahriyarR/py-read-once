PYTHON=./.venv/bin/python

PHONY = help install install-dev test format lint

help:
	@echo "---------------HELP-----------------"
	@echo "To install the project type -> make install"
	@echo "To install the project for development type -> make install-dev"
	@echo "To test the project type -> make test"
	@echo "To format code type -> make format"
	@echo "To check linter type -> make lint"
	@echo "------------------------------------"

install:
	${PYTHON} -m flit install --env --deps=develop

install-dev:
	${PYTHON} -m flit install --env --deps=develop --symlink


format:
	./scripts/format-imports.sh

lint:
	./scripts/lint.sh

test:
	pytest -svv