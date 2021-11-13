clean:	# Remove development artifacts
	@printf "Deleting Python artifacts...\n"
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -name '*~' -exec rm -f {} +
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@rm -rf dist .coverage htmlcov

lint:	# Lint code
	@isort --check .
	@black --check .
	@flake8

fix:	# Fix linting
	@isort .
	@black .

test:   # Run test suite and save coverage data
	@coverage run

coverage: test	# Run coverage report
	@coverage report

covhtml: test   # Run coverage and open HTML report
	@coverage html --fail-under=0
	@if command -v xdg-open > /dev/null; then xdg-open htmlcov/index.html; exit 1; fi  # Linux
	@if command -v open > /dev/null; then open htmlcov/index.html; exit 1; fi  # MacOS
