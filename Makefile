.PHONY: help format lint test clean install dev

help:  ## 显示帮助信息
	@echo "可用命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## 安装生产依赖
	pip install -r requirements.txt

install-lock:  ## 安装锁定版本依赖
	pip install -r requirements-lock.txt

dev:  ## 安装开发依赖
	pip install -r requirements-dev.txt
	pre-commit install

format:  ## 格式化代码
	black src/ tests/
	isort src/ tests/

lint:  ## 代码检查
	flake8 src/ tests/
	pylint src/

type-check:  ## 类型检查
	mypy src/

test:  ## 运行测试
	pytest tests/ -v --cov=src

test-report:  ## 运行测试并生成覆盖率报告
	pytest tests/ -v --cov=src --cov-report=html
	@echo "覆盖率报告已生成到 htmlcov/index.html"

clean:  ## 清理临时文件
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .mypy_cache/ .coverage htmlcov/

run:  ## 运行应用
	python src/main.py

build:  ## 构建应用
	./build_and_sign.sh
