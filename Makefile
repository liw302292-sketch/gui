SHELL := /bin/bash

.PHONY: help up down logs backend frontend seed test migrate revision reset-demo lint

help:
	@echo "make up            - 启动全套 Docker 服务 (frontend/backend/postgres/redis/nginx)"
	@echo "make down          - 停止并移除容器"
	@echo "make logs          - 查看日志"
	@echo "make migrate       - 执行数据库迁移"
	@echo "make seed          - 初始化演示数据"
	@echo "make reset-demo    - 重置演示数据库并重新灌入数据"
	@echo "make test          - 运行后端测试"
	@echo "make backend       - 本地启动后端 (venv)"
	@echo "make frontend      - 本地启动前端 (npm)"

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python seed.py

reset-demo:
	docker compose exec backend python seed.py --reset

test:
	docker compose exec backend pytest -q

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

lint:
	cd backend && ruff check . && mypy app || true
	cd frontend && npm run lint

