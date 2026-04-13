.PHONY: clean
clean:
	rm -f .DS_Store
	rm -rf .venv/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf __pycache__/
	rm -rf .ruff_cache/
	rm -rf frontend/node_modules/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

.PHONY: check
check:
	ruff check --fix
	ruff format
	pyright
