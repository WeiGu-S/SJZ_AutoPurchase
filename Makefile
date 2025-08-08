# 智能抢购助手开发工具

.PHONY: help install install-dev test test-unit test-integration lint format type-check clean build docs run-gui run-cli

# 默认目标
help:
	@echo "智能抢购助手开发工具"
	@echo ""
	@echo "可用命令:"
	@echo "  install        安装生产依赖"
	@echo "  install-dev    安装开发依赖"
	@echo "  test           运行所有测试"
	@echo "  test-unit      运行单元测试"
	@echo "  test-integration 运行集成测试"
	@echo "  lint           代码检查"
	@echo "  format         代码格式化"
	@echo "  type-check     类型检查"
	@echo "  clean          清理构建文件"
	@echo "  build          构建包"
	@echo "  docs           生成文档"
	@echo "  run-gui        运行GUI模式"
	@echo "  run-cli        运行CLI模式"

# 安装依赖
install:
	.venv/bin/pip install -r requirements.txt

install-dev:
	.venv/bin/pip install -r requirements-dev.txt

# 测试
test: test-unit test-integration

test-unit:
	.venv/bin/python -m pytest tests/test_*.py -v

test-integration:
	.venv/bin/python tests/test_integration.py

# 代码质量
lint:
	flake8 smart_buyer tests
	mypy smart_buyer

format:
	black smart_buyer tests
	isort smart_buyer tests

type-check:
	mypy smart_buyer

# 清理
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete

# 构建
build: clean
	python -m build

# 文档
docs:
	cd docs && make html

# 运行应用
run-gui:
	.venv/bin/python -m smart_buyer

run-cli:
	.venv/bin/python -m smart_buyer --console

# 开发模式安装
dev-install:
	.venv/bin/pip install -e .

# 发布到PyPI
upload-test:
	python -m twine upload --repository testpypi dist/*

upload:
	python -m twine upload dist/*

# 检查包
check:
	python -m twine check dist/*

# 完整的开发环境设置
setup-dev: install-dev dev-install
	@echo "开发环境设置完成！"

# 运行所有检查
check-all: lint type-check test
	@echo "所有检查通过！"