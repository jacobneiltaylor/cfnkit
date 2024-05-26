code:
    code {{ justfile_directory() }}

install:
    poetry install

format: install
    poetry run ruff format {{ justfile_directory() }}/src {{ justfile_directory() }}/test
    poetry run ruff check --fix {{ justfile_directory() }}/src {{ justfile_directory() }}/test

lint: install
    poetry run ruff check {{ justfile_directory() }}/src {{ justfile_directory() }}/test

typecheck: install
    poetry run mypy {{ justfile_directory() }}/src

debug-lint:
    poetry run ruff check --show-source -e {{ justfile_directory() }}/src {{ justfile_directory() }}/test

unit: install
    poetry run pytest --cov={{ justfile_directory() }}/src/cfnkit test/

build: install
    poetry build

publish: build
    poetry publish --skip-existing

sync-version:
    poetry set-git-version

install-poetry:
    pip3 install poetry
    poetry self add poetry-git-version-plugin

test: lint typecheck unit