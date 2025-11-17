.PHONY: help install install-dev test lint format clean run docker-build docker-up docker-down

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r bot/requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements-dev.txt
	pre-commit install

test: ## Run tests with coverage
	pytest --cov=bot --cov-report=html --cov-report=term-missing

test-fast: ## Run tests without coverage
	pytest -v

lint: ## Run linters
	black --check bot/ tests/
	flake8 bot/ tests/ --max-line-length=100
	mypy bot/ --ignore-missing-imports

format: ## Format code with black
	black bot/ tests/

clean: ## Clean cache and build files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

run: ## Run the bot locally
	python -m bot.main

db-recreate: ## Recreate database
	python recreate_db.py

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start services with Docker Compose
	docker-compose up -d

docker-down: ## Stop services
	docker-compose down

docker-logs: ## View logs
	docker-compose logs -f

docker-restart: ## Restart services
	docker-compose restart

docker-clean: ## Clean Docker resources
	docker-compose down -v
	docker system prune -f
