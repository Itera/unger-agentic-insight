.PHONY: help build start stop logs clean restart test

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build all Docker containers
	docker-compose build

start: ## Start all services
	docker-compose up -d

start-dev: ## Start all services with logs
	docker-compose up --build

stop: ## Stop all services
	docker-compose down

logs: ## View logs from all services
	docker-compose logs -f

logs-backend: ## View backend logs
	docker-compose logs -f backend

logs-frontend: ## View frontend logs
	docker-compose logs -f frontend

logs-adx: ## View ADX MCP service logs
	docker-compose logs -f adx-mcp

logs-db: ## View database logs
	docker-compose logs -f database

restart: ## Restart all services
	docker-compose down && docker-compose up --build -d

clean: ## Remove all containers, networks, and volumes
	docker-compose down -v --remove-orphans
	docker system prune -f

clean-all: ## Remove everything including images
	docker-compose down -v --remove-orphans --rmi all
	docker system prune -af

test-health: ## Test all service health endpoints
	@echo "Testing service health..."
	@curl -f http://localhost:8000/health || echo "Backend health check failed"
	@curl -f http://localhost:8001/health || echo "ADX MCP health check failed"
	@curl -f http://localhost:3000 || echo "Frontend health check failed"

shell-backend: ## Open shell in backend container
	docker-compose exec backend bash

shell-adx: ## Open shell in ADX MCP container
	docker-compose exec adx-mcp bash

shell-db: ## Open shell in database container
	docker-compose exec database psql -U postgres -d insight_db

setup: ## Initial setup - copy env file and build
	cp .env.example .env
	@echo "Please edit .env file with your OpenAI API key and ADX credentials"
	@echo "Then run: make start-dev"