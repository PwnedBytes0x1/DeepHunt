# DeepHunt Makefile
# Build, test, and package DeepHunt for distribution

.PHONY: help install install-dev build binary clean test lint format

PYTHON := python3
PIP := pip3
PROJECT := deephunt
DIST_DIR := dist
BUILD_DIR := build
SPEC_FILE := scripts/deephunt.spec

# Default target
help:
	@echo ""
	@echo "  \033[1;36mDeepHunt v1.0 - Build Automation\033[0m"
	@echo "  =================================="
	@echo ""
	@echo "  \033[1;33mAvailable Targets:\033[0m"
	@echo ""
	@echo "  \033[1;32mmake install\033[0m       Install production dependencies"
	@echo "  \033[1;32mmake install-dev\033[0m   Install with dev dependencies and tools"
	@echo "  \033[1;32mmake build\033[0m         Build wheel distribution"
	@echo "  \033[1;32mmake binary\033[0m        Compile standalone binary (requires PyInstaller)"
	@echo "  \033[1;32mmake binary-termux\033[0m Compile binary optimized for Termux/Android"
	@echo "  \033[1;32mmake test\033[0m          Run test suite"
	@echo "  \033[1;32mmake lint\033[0m          Run code quality checks"
	@echo "  \033[1;32mmake format\033[0m        Format code with black"
	@echo "  \033[1;32mmake clean\033[0m         Remove build artifacts"
	@echo "  \033[1;32mmake setup\033[0m         Full first-time setup"
	@echo ""

# Install production dependencies
install:
	$(PYTHON) -m pip install --upgrade pip setuptools wheel
	$(PYTHON) -m pip install -r requirements.txt

# Install with dev dependencies
install-dev: install
	$(PYTHON) -m pip install -e ".[dev]"

# Full setup
setup: install-dev
	@echo ""
	@echo "  \033[1;36mDeepHunt setup complete!\033[0m"
	@echo "  Run '\033[1;33mdhunt --help\033[0m' to get started"
	@echo ""

# Build wheel distribution
build:
	$(PYTHON) -m build
	@echo ""
	@echo "  \033[1;36mBuild complete!\033[0m Artifacts in \033[1;33mdist/\033[0m"
	@echo ""

# Compile standalone binary
binary:
	@echo "  \033[1;36mCompiling DeepHunt binary...\033[0m"
	$(PYTHON) -m PyInstaller $(SPEC_FILE) --clean --noconfirm
	@echo ""
	@echo "  \033[1;36mBinary compiled!\033[0m Location: \033[1;33mdist/dhunt\033[0m"
	@echo "  Install globally: \033[1;33msudo cp dist/dhunt /usr/local/bin/\033[0m"
	@echo "  Or for user:      \033[1;33mcp dist/dhunt ~/.local/bin/\033[0m"
	@echo ""

# Compile binary optimized for Termux
binary-termux:
	@echo "  \033[1;36mCompiling DeepHunt for Termux...\033[0m"
	$(PYTHON) -m PyInstaller $(SPEC_FILE) --clean --noconfirm \
		--distpath $(HOME)/.local/bin \
		--name dhunt-termux
	@echo ""
	@echo "  \033[1;36mTermux binary ready!\033[0m Location: \033[1;33m$$HOME/.local/bin/dhunt-termux\033[0m"
	@echo ""

# Run tests
test:
	pytest tests/ -v --tb=short --color=yes

# Code quality
lint:
	flake8 deephunt/ --max-line-length=100 --show-source --statistics
	mypy deephunt/ --ignore-missing-imports

# Format code
format:
	black deephunt/ tests/ --line-length=100

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR)/ $(DIST_DIR)/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.spec" ! -path "scripts/*" -delete
	@echo "  \033[1;32mCleaned build artifacts\033[0m"

# Development mode
dev:
	$(PYTHON) -m deephunt.cli $(ARGS)

# Termux-specific install (for use in Termux environment)
termux-install:
	@echo "  \033[1;36mInstalling DeepHunt in Termux...\033[0m"
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .
	@echo ""
	@echo "  \033[1;32mDeepHunt installed successfully!\033[0m"
	@echo "  Run: \033[1;33mdhunt --help\033[0m"
	@echo ""

# Quick install without optional dependencies
install-minimal:
	$(PYTHON) -m pip install --upgrade pip setuptools wheel
	$(PYTHON) -m pip install click rich aiohttp beautifulsoup4 pyyaml python-dotenv requests
