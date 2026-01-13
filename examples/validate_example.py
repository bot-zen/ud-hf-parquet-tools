"""
Example: Validate Parquet files against original CoNLL-U.
"""

import json
from pathlib import Path

from ud_hf_parquet_tools import validate_treebank

# Load metadata
metadata_file = Path("metadata-2.17.json")
with open(metadata_file) as f:
    metadata = json.load(f)

# Validate French-GSD
results = validate_treebank(
    name="fr_gsd",
    metadata=metadata["fr_gsd"],
    parquet_dir=Path("parquet"),
    ud_repos_dir=Path("UD_repos"),
    use_local=True,
    verbose=True
)

print(f"\nValidation Results:")
print(f"  Success: {results['success']}")
print(f"  Total sentences: {results['total_sentences']}")
print(f"  Total errors: {results['total_errors']}")

for split_name, split_results in results['splits'].items():
    if split_results.get('passed'):
        print(f"  ✓ {split_name}: {split_results['sentences']} sentences OK")
    else:
        print(f"  ✗ {split_name}: {split_results['errors']} errors")
