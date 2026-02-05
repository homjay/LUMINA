.PHONY: help install run test docker-build docker-up docker-down clean

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make run        - Run the server"
	@echo "  make test       - Run tests"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-up  - Start services with Docker Compose"
	@echo "  make docker-down - Stop Docker Compose services"
	@echo "  make clean      - Clean generated files"

install:
	pip install -r requirements.txt

run:
	python main.py

test:
	pytest tests/ -v

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	rm -rf data/*.json data/*.db logs/*.log __pycache__ app/__pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
