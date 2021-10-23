# contributing

## TL;DR

1. Clone repo
2. Install necessary tooling and deps
    ```shell
    make setup
    make dep
    ```

## Formatting and style guide

We are following [PEP8](https://www.python.org/dev/peps/pep-0008/) and
using [black](https://github.com/psf/black) [isort](https://github.com/PyCQA/isort)
and [flake8](https://github.com/PyCQA/flake8) for code style and formatting.

```shell
make lint # run linter
make lint-fix # run linters and formatters in fix mode
```

## Commit messages

We are following [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) specification.

Example:

```text
ci: add deployment script using helm
```

## pre-commit hook

We are using [pre-commit](https://pre-commit.com/) for running code formatters, code linters and commit message linters
before commit. Please make sure that you have it installed and enabled.
