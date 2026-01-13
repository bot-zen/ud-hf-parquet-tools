"""
Example: Generate Parquet files for a single treebank.
"""

import json
from pathlib import Path

from ud_hf_parquet_tools import generate_parquet_for_treebank

# Load metadata
metadata_file = Path("metadata-2.17.json")
with open(metadata_file) as f:
    metadata = json.load(f)

# Generate Parquet for French-GSD
success = generate_parquet_for_treebank(
    name="fr_gsd",
    metadata=metadata["fr_gsd"],
    ud_repos_dir=Path("UD_repos"),
    output_dir=Path("parquet"),
    verbose=True
)

if success:
    print("\n✓ Parquet generation successful!")
else:
    print("\n✗ Parquet generation failed")
