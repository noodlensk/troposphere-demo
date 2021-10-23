setup: ## Setup (Mac OS only)
	brew install cloudformation-guard
	brew install pre-commit
	pre-commit install
	pre-commit run --all-files
dep-dev: ## Download dev dependencies
	pip3 install -r dev-requirements.txt
dep: dep-dev ## Download dependencies
	pip3 install -r requirements.txt
lint: ## Lint
	black --check .
	isort --check-only .
	flake8 .
lint-fix: ## Fix errors from linter
	black .
	isort .
generate: ## Generate template
	python3 templates/resources.py
validate: generate ## Validate templates against rules
	cfn-guard validate -d templates/output/ -r validation/
clean: ## Remove generated templates
	rm -rf templates/output
# Absolutely awesome: http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
