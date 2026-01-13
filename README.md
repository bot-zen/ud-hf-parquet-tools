# UD-HF-Parquet-Tools

Tools for generating and validating Universal Dependencies datasets in Parquet format for HuggingFace.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Features

- **Generate Parquet files** from Universal Dependencies CoNLL-U data
- **Validate Parquet files** against original CoNLL-U with 100% fidelity checking
- **Handle CoNLL-U edge cases**: double equals bug, duplicate metadata keys, empty nodes, MWTs
- **CLI and Python API** for programmatic use
- **Comprehensive test suite** with 60+ tests

## Installation

Using `uv` (recommended):

```bash
uv pip install ud-hf-parquet-tools
```

Using `pip`:

```bash
pip install ud-hf-parquet-tools
```

## Quick Start

### Command Line Interface

Generate Parquet files:

```bash
# Generate for all treebanks
ud-hfp-tools generate --metadata metadata.json --output-dir parquet/

# Generate for specific treebanks
ud-hfp-tools generate --metadata metadata.json --treebanks fr_gsd,en_ewt --output-dir parquet/

# Test mode (3 treebanks only)
ud-hfp-tools generate --metadata metadata.json --test
```

Validate Parquet files:

```bash
# Validate from local files
ud-hfp-tools validate --local --metadata metadata.json

# Validate specific treebanks
ud-hfp-tools validate --local --treebanks fr_gsd,en_ewt

# Validate from HuggingFace Hub
ud-hfp-tools validate --revision 2.17 --treebanks fr_gsd
```

### Python API

Generate Parquet files:

```python
from ud_hf_parquet_tools import generate_parquet_for_treebank
from pathlib import Path
import json

# Load metadata
with open("metadata.json") as f:
    metadata = json.load(f)

# Generate for one treebank
success = generate_parquet_for_treebank(
    name="fr_gsd",
    metadata=metadata["fr_gsd"],
    ud_repos_dir=Path("UD_repos"),
    output_dir=Path("parquet"),
    verbose=True
)
```

Validate Parquet files:

```python
from ud_hf_parquet_tools import validate_treebank
from pathlib import Path
import json

# Load metadata
with open("metadata.json") as f:
    metadata = json.load(f)

# Validate one treebank
results = validate_treebank(
    name="fr_gsd",
    metadata=metadata["fr_gsd"],
    parquet_dir=Path("parquet"),
    ud_repos_dir=Path("UD_repos"),
    verbose=True
)

print(f"Success: {results['success']}")
print(f"Total sentences: {results['total_sentences']}")
print(f"Total errors: {results['total_errors']}")
```

## CoNLL-U Parsing Features

This library handles several CoNLL-U parsing edge cases to ensure 100% fidelity:

### 1. Double Equals Bug
The `conllu` library fails to parse values starting with `=`:
- Example: `Gloss==POSS` becomes `{'Gloss': None}` instead of `{'Gloss': '=POSS'}`
- **Solution**: Direct raw field extraction bypasses the parser

### 2. Duplicate Metadata Keys
Some treebanks have multiple entries with the same key (e.g., multiple `# media` lines):
- **Problem**: Dictionary-based storage keeps only the last value
- **Solution**: Preserve metadata as ordered list with special markers

### 3. Empty Metadata Values
Lines like `# text_en =` (with empty value) are ignored by the parser:
- **Solution**: Raw comment extraction preserves all metadata

### 4. Keys Without Values
Comments like `# newpar` without `=` become `{'newpar': None}`:
- **Solution**: Store as just `"newpar"` (not `"newpar = None"`)

### 5. Multi-Word Tokens (MWTs)
Contractions like "du" → "de le" (French) with ID `1-2`:
- Stored with tuple IDs like `(1, '-', 2)`
- Preserved with form, FEATS (for `Typo=Yes`), and MISC

### 6. Empty Nodes
Enhanced dependencies with decimal IDs like `22.1`:
- Stored with tuple IDs like `(22, '.', 1)`
- Full 10-field preservation including all annotations

## Dataset Schema

Generated Parquet files include:

```python
{
    "sent_id": str,              # Sentence ID
    "text": str,                 # Full sentence text
    "comments": [str],           # Metadata comments (ordered, with duplicates)
    "tokens": [str],             # Word forms (syntactic words only)
    "lemmas": [str],             # Lemmas
    "upos": [str],               # Universal POS tags (ClassLabel)
    "xpos": [str],               # Language-specific POS
    "feats": [str],              # Morphological features
    "head": [str],               # Dependency heads
    "deprel": [str],             # Dependency relations
    "deps": [str],               # Enhanced dependencies
    "misc": [str],               # Miscellaneous annotations
    "mwt": [{                    # Multi-word tokens
        "id": str,                 # e.g., "1-2"
        "form": str,
        "feats": str,              # Optional (for Typo=Yes)
        "misc": str
    }],
    "empty_nodes": [{            # Empty nodes (enhanced deps)
        "id": str,                 # e.g., "22.1"
        "form": str,
        # ... all 10 CoNLL-U fields
    }]
}
```

## Documentation

- **[RELEASE.md](RELEASE.md)**: Complete guide for publishing new releases
  - Pre-release checklist
  - Version numbering guidelines
  - Git tagging and PyPI publishing workflow
  - Troubleshooting guide

- **[CHANGELOG.md](CHANGELOG.md)**: Version history and release notes

- **[INSTALLATION.md](INSTALLATION.md)**: Detailed installation instructions

- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Guidelines for contributors

## Development

Clone and install with development dependencies:

```bash
git clone https://github.com/egon-stemle/ud-hf-parquet-tools
cd ud-hf-parquet-tools
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=ud_hf_parquet_tools --cov-report=html
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Author

Egon W. Stemle <egon.stemle@eurac.edu>

## Acknowledgments

This library was developed for the [Universal Dependencies](https://universaldependencies.org/) project to enable efficient distribution of UD treebanks via HuggingFace Datasets.
