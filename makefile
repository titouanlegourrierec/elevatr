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

precommit:
	prek run --all-files

clean:
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +

help:
	@echo "\033[1;36mMakefile targets:\033[0m"
	@echo "  \033[1;32mlint\033[0m     : Check code with ruff."
	@echo "  \033[1;32mformat\033[0m   : Format code with ruff."
	@echo "  \033[1;32mtypecheck\033[0m: Type check code with ty."
	@echo "  \033[1;32mquality\033[0m  : Run lint, format, and typecheck."
	@echo "  \033[1;32mtest\033[0m     : Run tests with pytest."
	@echo "  \033[1;32mprecommit\033[0m: Run pre-commit hooks on all files."
	@echo "  \033[1;32mclean\033[0m    : Remove temporary files."
