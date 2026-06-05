# Contributing to DeepHunt

First off, thank you for considering contributing to DeepHunt! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Respect security disclosure practices
- Follow responsible disclosure for any vulnerabilities found

## How Can I Contribute?

### Reporting Bugs

Before creating a bug report, please check existing issues. When creating a report, include:

- **Termux/Android version**
- **Python version**
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Error logs** (run with `-v` flag)

```bash
# Get system info for bug reports
dhunt check
```

### Suggesting Features

Feature suggestions are welcome! Open an issue with:

- Clear description of the feature
- Use case and motivation
- Proposed implementation (optional)

### Creating Skills

Skills are the easiest way to contribute! See the [Skills System](#skills-system) section below.

### Code Contributions

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make test`)
5. Commit your changes
6. Push to your fork
7. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/deephunt.git
cd deephunt

# Install dev dependencies
make install-dev

# Or manually:
pip install -e ".[dev,telegram]"

# Run tests
make test

# Format code
make format

# Run linter
make lint
```

## Project Structure

```
deeephunt/
├── deephunt/           # Main package
│   ├── __init__.py
│   ├── cli.py          # CLI entry point
│   ├── core/           # Core framework
│   │   ├── identity.py
│   │   ├── config.py
│   │   ├── scope.py
│   │   └── orchestrator.py
│   ├── agents/         # Agent implementations
│   │   ├── recon_agent.py
│   │   ├── vuln_id_agent.py
│   │   └── skill_builder_agent.py
│   ├── skills/         # Bundled skills
│   │   └── loader.py
│   └── utils/          # Utilities
│       ├── banner.py
│       ├── logger.py
│       └── termux.py
├── skills/             # Skill definitions
│   ├── recon/
│   ├── exploitation/
│   ├── reporting/
│   ├── payloads/
│   ├── network/
│   └── post_exploitation/
├── tests/              # Test suite
├── scripts/            # Build scripts
├── requirements.txt
├── pyproject.toml
├── Makefile
├── README.md
└── CONTRIBUTIONS.md    # This file
```

## Skills System

### Skill File Format

Skills are Markdown files with YAML frontmatter:

```markdown
---
name: Skill Name
category: category_name
version: "1.0"
author: "Your Handle"
description: "What this skill does"
commands:
  - tool1
  - tool2
tags:
  - tag1
  - tag2
---

# Skill Title

## Description

Your skill documentation in Markdown...

## Usage

```bash
example command
```

## Notes
- Important considerations
```

### Skill Categories

| Category | Description |
|----------|-------------|
| `recon` | Reconnaissance techniques |
| `exploitation` | Exploitation methods |
| `reporting` | Report templates and formats |
| `payloads` | Payload collections |
| `network` | Network-level attacks |
| `post_exploitation` | Post-exploitation techniques |
| `custom` | User-defined skills |

### Skill Location

Skills can be placed in:

1. **Workspace skills**: `~/deephunt/skills/` (user-created, persistent)
2. **Nested categories**: `~/deephunt/skills/<category>/<skill>.md`
3. **Bundled skills**: `deephunt/skills/` (shipped with package)

### Skill Loading Order

1. User workspace skills take priority
2. Nested directory skills are discovered automatically
3. Bundled skills are used as fallback

## Code Style

- **Python**: Follow PEP 8 with 100-character line limit
- **Formatting**: Use `black` (run `make format`)
- **Imports**: Group as stdlib, third-party, local
- **Types**: Use type hints where practical
- **Docstrings**: Google-style docstrings

## Testing

```bash
# Run all tests
make test

# Run specific test
pytest tests/test_scope.py -v

# With coverage
pytest --cov=deephunt --cov-report=html
```

## Commit Message Format

```
type(scope): subject

body (optional)

footer (optional)
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(skills): add SSRF detection skill
fix(termux): correct battery status parsing
docs(readme): update installation instructions
```

## Pull Request Process

1. Update README.md with details of changes if applicable
2. Update documentation for any new features
3. Add tests for new functionality
4. Ensure all tests pass
5. Update the version if applicable
6. Request review from maintainers

## Security

For security issues, please email **security@deephunt.dev** instead of opening a public issue.

## Recognition

Contributors will be:
- Listed in the project's CONTRIBUTORS file
- Mentioned in release notes for significant contributions
- Credited in skill files they create

## Questions?

- Open a [GitHub Discussion](https://github.com/PwnedBytes0x1/deephunt/discussions)
- Join our community chat (link in README)

Thank you for contributing to DeepHunt!
