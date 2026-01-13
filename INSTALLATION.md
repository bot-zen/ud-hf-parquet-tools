# Installation Guide

## Requirements

- Python 3.12 or higher
- `uv` package manager (recommended) or `pip`

## Installation Methods

### Option 1: Install from source with uv (recommended)

```bash
# Clone the repository
git clone https://github.com/egon-stemle/ud-hf-parquet-tools
cd ud-hf-parquet-tools

# Create virtual environment and install
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### Option 2: Install from source with pip

```bash
# Clone the repository
git clone https://github.com/egon-stemle/ud-hf-parquet-tools
cd ud-hf-parquet-tools

# Create virtual environment and install
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### Option 3: Install from PyPI (future)

```bash
# With uv
uv pip install ud-hf-parquet-tools

# With pip
pip install ud-hf-parquet-tools
```

## Verify Installation

Check that the CLI is available:

```bash
ud-tools --help
```

You should see:

```
usage: ud-tools [-h] {generate,validate} ...

Tools for generating and validating Universal Dependencies Parquet datasets

positional arguments:
  {generate,validate}  Command to run
    generate           Generate Parquet files from CoNLL-U data
    validate           Validate Parquet files against CoNLL-U
```

## Development Installation

For development with tests and linting:

```bash
# Install with development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src/ tests/
```

## Dependencies

The library requires:

- `conllu>=5.0.0` - CoNLL-U parsing
- `datasets>=4.0.0` - HuggingFace datasets
- `pyarrow>=14.0.0` - Parquet support
- `pyyaml>=6.0.2` - YAML configuration
- `python-dotenv>=1.0.0` - Environment variables

Development dependencies:

- `pytest>=7.0.0` - Testing
- `pytest-cov>=4.0.0` - Coverage
- `ruff>=0.1.0` - Linting

## Troubleshooting

### Command not found: ud-tools

If `ud-tools` is not found after installation, ensure your virtual environment is activated:

```bash
source .venv/bin/activate
```

### Import errors

If you get import errors, make sure you installed the package:

```bash
uv pip list | grep ud-hf-parquet-tools
```

### Python version issues

Verify you're using Python 3.12+:

```bash
python --version
```

## Next Steps

- Read the [README.md](README.md) for usage examples
- Check [examples/](examples/) for code samples
- See [CONTRIBUTING.md](CONTRIBUTING.md) for development guide
