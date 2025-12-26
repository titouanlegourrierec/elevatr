.PHONY: lint format typecheck quality clean

SRC=elevatr tests

lint:
	ruff check --fix $(SRC)

format:
	ruff format $(SRC)

typecheck:
	ty check $(SRC)

quality: lint format typecheck

test:
	pytest -n auto tests/

clean:
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +
