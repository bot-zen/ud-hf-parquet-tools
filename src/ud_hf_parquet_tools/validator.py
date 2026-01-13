"""
Parquet validation module for Universal Dependencies datasets.

This module validates Parquet files by comparing them with original CoNLL-U data.
"""

import difflib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from datasets import load_dataset

from .conllu_utils import example_to_conllu


def normalize_conllu(text: str) -> str:
    """Normalize CoNLL-U text for comparison (strip trailing blank lines)."""
    lines = text.strip().split('\n')
    while lines and lines[-1] == '':
        lines.pop()
    return '\n'.join(lines) + '\n'


def validate_treebank_text(
    name: str,
    metadata: Dict[str, Any],
    parquet_dir: Path | str,
    ud_repos_dir: Path,
    verbose: bool = True,
    very_verbose: bool = False
) -> Dict[str, Any]:
    """
    Validate a single treebank using text-based comparison with unified diff.

    Args:
        name: Treebank name (e.g., "fr_gsd")
        metadata: Treebank metadata including splits and file paths
        parquet_dir: Path to parquet directory (local Path or HF Hub string)
        ud_repos_dir: Path to UD repositories directory
        verbose: Print progress messages
        very_verbose: Print all differences (not just first 20 lines)

    Returns:
        Validation results dictionary
    """
    results = {
        'name': name,
        'splits': {},
        'total_sentences': 0,
        'total_errors': 0,
        'success': True
    }

    if verbose:
        print(f"  Text-based comparison...")

    # Check if parquet directory exists for local validation
    treebank_parquet_dir = parquet_dir / name
    if isinstance(parquet_dir, Path) and not treebank_parquet_dir.exists():
        results['success'] = False
        results['error'] = f"Parquet directory not found: {treebank_parquet_dir}"
        if verbose:
            print(f"    ERROR: {results['error']}")
        return results

    # Process each split
    for split_name, split_data in metadata.get("splits", {}).items():
        if isinstance(parquet_dir, Path):
            parquet_file = treebank_parquet_dir / f"{split_name}.parquet"
            if not parquet_file.exists():
                continue
            parquet_path = str(parquet_file)
        else:
            # HF Hub path
            parquet_path = f"{parquet_dir}/{name}/{split_name}.parquet"

        try:
            # Load parquet dataset
            ds = load_dataset('parquet', data_files={split_name: parquet_path})
            dataset = ds[split_name]
        except Exception as e:
            results['success'] = False
            results['splits'][split_name] = {
                'error': f"Failed to load parquet: {e}",
                'sentences': 0,
                'errors': 0
            }
            continue

        # Get UPOS names for ClassLabel conversion
        upos_names = dataset.features['upos'].feature.names

        # Reconstruct all examples to CoNLL-U
        reconstructed_conllu = ""
        for example in dataset:
            reconstructed_conllu += example_to_conllu(example, upos_names)

        # Load original CoNLL-U files
        original_conllu = ""
        files = split_data.get("files", [])
        if not files:
            results['splits'][split_name] = {
                'error': f"No files found in metadata",
                'sentences': 0,
                'errors': 0
            }
            continue

        for file_path in files:
            # Extract just the filename from the path
            filename = Path(file_path).name

            # Construct full path: UD_repos/dirname/filename
            full_path = ud_repos_dir / metadata["dirname"] / filename

            if not full_path.exists():
                results['success'] = False
                results['splits'][split_name] = {
                    'error': f"Original file not found: {full_path}",
                    'sentences': 0,
                    'errors': 0
                }
                continue

            # Read original file
            with open(full_path, 'r', encoding='utf-8') as f:
                original_conllu += f.read()

        # Normalize both for comparison
        original_normalized = normalize_conllu(original_conllu)
        reconstructed_normalized = normalize_conllu(reconstructed_conllu)

        # Compare
        num_sentences = len(dataset)
        results['total_sentences'] += num_sentences

        if original_normalized == reconstructed_normalized:
            results['splits'][split_name] = {
                'sentences': num_sentences,
                'errors': 0,
                'passed': True
            }
            if verbose:
                print(f"    ✅ {split_name}: {num_sentences} sentences match perfectly")
        else:
            results['success'] = False

            # Find differences (use n=1 for minimal context)
            original_lines = original_normalized.split('\n')
            reconstructed_lines = reconstructed_normalized.split('\n')

            diff = list(difflib.unified_diff(
                original_lines,
                reconstructed_lines,
                fromfile=f'original_{split_name}',
                tofile=f'reconstructed_{split_name}',
                lineterm='',
                n=1  # Show only 1 line of context (instead of default 3)
            ))

            num_diff_lines = len([l for l in diff if l.startswith('+') or l.startswith('-')])
            results['total_errors'] += num_diff_lines

            results['splits'][split_name] = {
                'sentences': num_sentences,
                'errors': num_diff_lines,
                'diff': diff,  # Store all diff lines for very_verbose mode
                'passed': False
            }

            if verbose:
                print(f"    ❌ {split_name}: Found {num_diff_lines} different lines")
                if very_verbose:
                    print(f"       All differences:")
                    for line in diff:
                        print(f"         {line}")
                else:
                    print(f"       First differences (use -vv to see all):")
                    for line in diff[:20]:
                        print(f"         {line}")
                    if len(diff) > 20:
                        print(f"         ... ({len(diff) - 20} more diff lines)")

    return results


def validate_treebank(
    name: str,
    metadata: Dict[str, Any],
    parquet_dir: Path | str,
    ud_repos_dir: Path,
    use_local: bool = False,
    revision: str = "2.17",
    mode: str = "text",
    verbose: bool = True,
    very_verbose: bool = False
) -> Dict[str, Any]:
    """
    Validate a single treebank.

    Args:
        name: Treebank name (e.g., "fr_gsd")
        metadata: Treebank metadata
        parquet_dir: Path to parquet directory (local Path or HF Hub string)
        ud_repos_dir: Path to UD repositories directory
        use_local: Load from local parquet files instead of HF Hub
        revision: HuggingFace Hub revision (used to construct path if not use_local)
        mode: Comparison mode ('text', 'field', or 'both')
        verbose: Print progress messages
        very_verbose: Print all differences (not just first 20 lines)

    Returns:
        Validation results dictionary
    """
    if verbose:
        source = "local parquet" if use_local else f"HF Hub (revision={revision})"
        print(f"\nValidating {name} from {source}...")

    # Construct parquet path if not using local files
    if not use_local:
        parquet_dir = f"hf://datasets/commul/universal_dependencies@{revision}/parquet"

    # Run text-based validation (default and recommended)
    if mode in ('text', 'both'):
        results = validate_treebank_text(
            name,
            metadata,
            parquet_dir,
            ud_repos_dir,
            verbose,
            very_verbose
        )
    else:
        results = {
            'name': name,
            'splits': {},
            'total_sentences': 0,
            'total_errors': 0,
            'success': True
        }

    # Note: field-by-field mode could be added here if needed
    # For now, text mode is the primary validation method as it tests
    # the actual production reconstruction logic

    return results


