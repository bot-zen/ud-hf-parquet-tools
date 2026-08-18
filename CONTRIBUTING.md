# Contributing to UD-HF-Parquet-Tools

Thank you for considering contributing to this project!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/bot-zen/ud-hf-parquet-tools
cd ud-hf-parquet-tools
```

2. Create a virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

## Running Tests

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=ud_hf_parquet_tools --cov-report=html
open htmlcov/index.html  # View coverage report
```

Run specific test file:
```bash
pytest tests/test_parsing.py -v
```

## Code Style

We use `ruff` for linting:
```bash
ruff check src/ tests/
ruff format src/ tests/
```

## Making Changes

1. Create a new branch for your feature:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and add tests

3. Ensure tests pass:
```bash
pytest
```

4. Commit your changes:
```bash
git add .
git commit -m "Description of your changes"
```

5. Push and create a pull request

## Project Structure

```
ud-hf-parquet-tools/
├── src/ud_hf_parquet_tools/
│   ├── __init__.py          # Public API
│   ├── conllu_utils.py      # CoNLL-U utilities
│   ├── generator.py         # Parquet generation
│   ├── validator.py         # Validation logic
│   └── cli.py               # Command-line interface
└── tests/                   # Test suite
```

## Reporting Issues

Please report issues on GitHub with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (Python version, OS, etc.)

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
