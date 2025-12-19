.PHONY: help install dev test lint format docker-up docker-down clean

# Default target
help:
	@echo "CloudGate API Gateway - Development Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install       Install dependencies"
	@echo "  dev           Start development environment"
	@echo "  test          Run tests with coverage"
	@echo "  lint          Run linters"
	@echo "  format        Format code"
	@echo "  docker-up     Start Docker containers"
	@echo "  docker-down   Stop Docker containers"
	@echo "  clean         Clean up generated files"

# Install dependencies
install:
	pip install -e ".[dev]"
	pre-commit install

# Start development environment
dev:
	docker-compose up -d postgres redis
	@echo "Waiting for services to be ready..."
	sleep 5
	uvicorn services.gateway.main:app --reload --port 8000 &
	uvicorn services.auth.main:app --reload --port 8001

# Run tests
test:
	pytest tests/ -v --cov=services --cov=shared --cov-report=html --cov-report=term-missing

# Run tests with specific markers
test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v

# Run linters
lint:
	ruff check .
	mypy services shared --ignore-missing-imports --explicit-package-bases

format-check:
	black --check .

typecheck:
	mypy services shared

frontend-build:
	cd services/gateway/static && npm install && npm run build

# Format code
format:
	black .
	ruff check . --fix

# Start Docker containers
docker-up:
	docker-compose up -d --build

# Stop Docker containers
docker-down:
	docker-compose down -v

# View logs
logs:
	docker-compose logs -f

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete

# Database migrations
migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(msg)"

# Build Docker images
build:
	docker build -f docker/Dockerfile.gateway -t cloudgate-gateway:latest --target production .
	docker build -f docker/Dockerfile.auth -t cloudgate-auth:latest --target production .

# Performance benchmarks (requires wrk or hey installed)
bench-local:
	@echo "Running local benchmarks..."
	@echo "Gateway health:"
	@wrk -t4 -c64 -d10s http://localhost:8000/health 2>/dev/null || echo "Install wrk: https://github.com/wg/wrk"
	@echo ""
	@echo "Auth health:"
	@wrk -t4 -c64 -d10s http://localhost:8001/health 2>/dev/null || echo "Install wrk: https://github.com/wg/wrk"

# Terraform commands
tf-init:
	cd infrastructure/terraform && terraform init

tf-plan:
	cd infrastructure/terraform && terraform plan -var-file="environments/dev.tfvars"

tf-apply:
	cd infrastructure/terraform && terraform apply -var-file="environments/dev.tfvars"

tf-destroy:
	cd infrastructure/terraform && terraform destroy -var-file="environments/dev.tfvars"
