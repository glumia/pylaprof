clean:	# Remove development artifacts
	@printf "Deleting Python artifacts...\n"
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -name '*~' -exec rm -f {} +
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@rm -rf dist

lint:	# Lint code
	@isort --check .
	@black --check .
	@flake8

fix:	# Fix linting
	@isort .
	@black .
