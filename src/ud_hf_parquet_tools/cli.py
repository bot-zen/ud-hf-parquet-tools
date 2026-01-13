"""
Command-line interface for UD-HF-Parquet-Tools.
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

from .generator import generate_parquet_for_treebank
from .validator import compare_parquet_tables, validate_treebank


def generate_command(args):
    """Handle the generate command."""
    # Load metadata
    metadata_file = Path(args.metadata)
    if not metadata_file.exists():
        print(f"Error: Metadata file not found: {metadata_file}", file=sys.stderr)
        return 1
    
    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    # Load blocked treebanks if provided
    blocked_treebanks = {}
    if args.blocked_treebanks:
        blocked_file = Path(args.blocked_treebanks)
        if blocked_file.exists():
            with open(blocked_file, "r", encoding="utf-8") as f:
                blocked_data = yaml.safe_load(f)
                if blocked_data:
                    blocked_treebanks = {k: v for k, v in blocked_data.items() if v is not None}
    
    verbose = args.verbose and not args.quiet

    if verbose:
        print(f"Loaded metadata for {len(metadata)} treebanks")
        if blocked_treebanks:
            print(f"Blocked treebanks: {len(blocked_treebanks)} ({', '.join(sorted(blocked_treebanks.keys()))})")
        print(f"Output directory: {args.output_dir}")
        print()
    
    # Determine which treebanks to process
    if args.test:
        treebanks_to_process = ["fr_gsd", "en_ewt", "it_isdt"]
        treebanks_to_process = [t for t in treebanks_to_process if t in metadata]
        if verbose:
            print(f"TEST MODE: Processing {len(treebanks_to_process)} treebanks")
    elif args.treebanks:
        treebanks_to_process = [t.strip() for t in args.treebanks.split(",")]
        treebanks_to_process = [t for t in treebanks_to_process if t in metadata]
        if verbose:
            print(f"Processing {len(treebanks_to_process)} specified treebanks")
    else:
        treebanks_to_process = sorted(metadata.keys())
        if verbose:
            print(f"Processing all {len(treebanks_to_process)} treebanks")
    
    # Filter out blocked treebanks
    if blocked_treebanks:
        original_count = len(treebanks_to_process)
        treebanks_to_process = [t for t in treebanks_to_process if t not in blocked_treebanks]
        skipped_count = original_count - len(treebanks_to_process)
        if skipped_count > 0 and verbose:
            print(f"Skipping {skipped_count} blocked treebank(s) due to license restrictions")
            for blocked in sorted(blocked_treebanks.keys()):
                if blocked in metadata:
                    reason = blocked_treebanks[blocked].get('reason', 'Unknown')
                    license_type = blocked_treebanks[blocked].get('license', 'Unknown')
                    print(f"  - {blocked}: {reason} (License: {license_type})")
    
    if verbose:
        print()
    
    # Process treebanks
    success_count = 0
    fail_count = 0
    
    for i, name in enumerate(treebanks_to_process, 1):
        if verbose:
            print(f"[{i}/{len(treebanks_to_process)}] {name}")
        
        try:
            success = generate_parquet_for_treebank(
                name=name,
                metadata=metadata[name],
                ud_repos_dir=Path(args.ud_repos_dir),
                output_dir=Path(args.output_dir),
                verbose=verbose,
                overwrite=args.overwrite
            )
            
            if success:
                success_count += 1
            else:
                fail_count += 1
        
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            fail_count += 1
        
        if verbose:
            print()
    
    # Summary
    if verbose:
        print("=" * 60)
        print(f"Completed: {success_count} successful, {fail_count} failed")
        
        output_path = Path(args.output_dir)
        if output_path.exists():
            total_size = sum(f.stat().st_size for f in output_path.rglob('*.parquet'))
            print(f"Total output size: {total_size / 1024 / 1024:.2f} MB")
    
    return 0 if fail_count == 0 else 1


def validate_command(args):
    """Handle the validate command."""
    # Validate argument compatibility
    if args.parquet_dir:
        # --parquet-dir implies --local
        args.local = True
        # Check if --revision was explicitly changed from default
        if args.revision != "2.17":
            print("Error: --parquet-dir and --revision are incompatible", file=sys.stderr)
            print("  Use --parquet-dir for local validation OR --revision for HF Hub", file=sys.stderr)
            return 1

    # Set default parquet-dir if using local mode
    if args.local and not args.parquet_dir:
        args.parquet_dir = "parquet"

    # Load metadata
    metadata_file = Path(args.metadata)
    if not metadata_file.exists():
        print(f"Error: Metadata file not found: {metadata_file}", file=sys.stderr)
        return 1

    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    verbose = args.verbose and not args.quiet
    very_verbose = args.very_verbose
    
    if verbose:
        print("=" * 60)
        print("Universal Dependencies Parquet Validation")
        print("=" * 60)
        print(f"Loaded metadata for {len(metadata)} treebanks")
        if args.local:
            print(f"Source: Local parquet files ({args.parquet_dir})")
        else:
            print(f"Source: HuggingFace Hub (revision={args.revision})")
        print(f"UD repos directory: {args.ud_repos_dir}")
        print()
    
    # Determine which treebanks to validate
    if args.test:
        treebanks_to_validate = ["fr_gsd", "en_ewt", "it_isdt"]
        treebanks_to_validate = [t for t in treebanks_to_validate if t in metadata]
        if verbose:
            print(f"TEST MODE: Validating {len(treebanks_to_validate)} treebanks")
    elif args.treebanks:
        treebanks_to_validate = [t.strip() for t in args.treebanks.split(",")]
        treebanks_to_validate = [t for t in treebanks_to_validate if t in metadata]
        if verbose:
            print(f"Validating {len(treebanks_to_validate)} specified treebanks")
    else:
        treebanks_to_validate = sorted(metadata.keys())
        if verbose:
            print(f"Validating all {len(treebanks_to_validate)} treebanks")
    
    # Validate treebanks
    success_count = 0
    fail_count = 0
    all_results = []
    
    for i, name in enumerate(treebanks_to_validate, 1):
        if verbose:
            print(f"\n[{i}/{len(treebanks_to_validate)}] {name}")
        
        try:
            results = validate_treebank(
                name=name,
                metadata=metadata[name],
                parquet_dir=Path(args.parquet_dir),
                ud_repos_dir=Path(args.ud_repos_dir),
                use_local=args.local,
                revision=args.revision,
                verbose=verbose,
                very_verbose=very_verbose
            )
            
            all_results.append(results)
            
            if results['success']:
                success_count += 1
            else:
                fail_count += 1
        
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            fail_count += 1
    
    # Summary
    if verbose:
        print()
        print("=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {success_count}")
        print(f"❌ Failed: {fail_count}")
        print(f"Total: {success_count + fail_count}")

        total_sentences = sum(r['total_sentences'] for r in all_results)
        total_errors = sum(r['total_errors'] for r in all_results)

        # Calculate metadata vs token errors
        total_metadata_errors = 0
        total_token_errors = 0
        for result in all_results:
            for split_data in result.get('splits', {}).values():
                if isinstance(split_data, dict):
                    total_metadata_errors += split_data.get('metadata_errors', 0)
                    total_token_errors += split_data.get('token_errors', 0)

        print(f"\nTotal sentences validated: {total_sentences:,}")
        print(f"Total errors found: {total_errors:,}")
        print(f"  - Token line errors: {total_token_errors:,}")
        print(f"  - Metadata line errors: {total_metadata_errors:,}")
        print()

        if fail_count == 0:
            print("🎉 SUCCESS: All parquet files validated successfully!")
        elif total_token_errors == 0:
            print("✅ All token lines match perfectly!")
            print("⚠️  Only metadata differences found (may be formatting/order issues).")
        else:
            print("⚠️  VALIDATION FAILED: Token line differences found.")
    
    return 0 if fail_count == 0 else 1


def compare_command(args):
    """Handle the compare command."""
    # Load metadata
    metadata_file = Path(args.metadata)
    if not metadata_file.exists():
        print(f"Error: Metadata file not found: {metadata_file}", file=sys.stderr)
        return 1

    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    verbose = args.verbose and not args.quiet

    if verbose:
        print("=" * 60)
        print("Universal Dependencies Parquet Comparison")
        print("=" * 60)
        print(f"Loaded metadata for {len(metadata)} treebanks")
        print(f"Directory 1: {args.parquet_dir1}")
        print(f"Directory 2: {args.parquet_dir2}")
        print()

    # Determine which treebanks to compare
    if args.test:
        treebanks_to_compare = ["fr_gsd", "en_ewt", "it_isdt"]
        treebanks_to_compare = [t for t in treebanks_to_compare if t in metadata]
        if verbose:
            print(f"TEST MODE: Comparing {len(treebanks_to_compare)} treebanks")
    elif args.treebanks:
        treebanks_to_compare = [t.strip() for t in args.treebanks.split(",")]
        treebanks_to_compare = [t for t in treebanks_to_compare if t in metadata]
        if verbose:
            print(f"Comparing {len(treebanks_to_compare)} specified treebanks")
    else:
        treebanks_to_compare = sorted(metadata.keys())
        if verbose:
            print(f"Comparing all {len(treebanks_to_compare)} treebanks")

    # Compare treebanks
    match_count = 0
    mismatch_count = 0
    all_results = []

    for i, name in enumerate(treebanks_to_compare, 1):
        if verbose:
            print(f"\n[{i}/{len(treebanks_to_compare)}] {name}")

        try:
            results = compare_parquet_tables(
                name=name,
                metadata=metadata[name],
                parquet_dir1=Path(args.parquet_dir1),
                parquet_dir2=Path(args.parquet_dir2),
                verbose=verbose
            )

            all_results.append(results)

            if results['success']:
                match_count += 1
            else:
                mismatch_count += 1

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            mismatch_count += 1

    # Summary
    if verbose:
        print()
        print("=" * 60)
        print("COMPARISON SUMMARY")
        print("=" * 60)
        print(f"✅ Matched: {match_count}")
        print(f"❌ Mismatched: {mismatch_count}")
        print(f"Total: {match_count + mismatch_count}")

        total_splits = sum(r.get('total_splits', 0) for r in all_results)
        total_matches = sum(r.get('total_matches', 0) for r in all_results)
        total_mismatches = sum(r.get('total_mismatches', 0) for r in all_results)

        print(f"\nTotal splits compared: {total_splits:,}")
        print(f"Split matches: {total_matches:,}")
        print(f"Split mismatches: {total_mismatches:,}")
        print()

        if mismatch_count == 0:
            print("🎉 SUCCESS: All parquet files match perfectly!")
        else:
            print("⚠️  COMPARISON FAILED: Some files differ.")

    return 0 if mismatch_count == 0 else 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="ud-hfp-tools",
        description="Tools for generating and validating Universal Dependencies Parquet datasets"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate Parquet files from CoNLL-U data")
    gen_parser.add_argument("--metadata", required=True, help="Path to metadata JSON file")
    gen_parser.add_argument("--ud-repos-dir", default="UD_repos", help="Path to UD repositories directory")
    gen_parser.add_argument("--output-dir", default="parquet", help="Output directory for Parquet files")
    gen_parser.add_argument("--blocked-treebanks", help="Path to blocked treebanks YAML file")
    gen_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing parquet files (default: skip)")
    gen_parser.add_argument("--test", action="store_true", help="Test mode: process 3 treebanks only")
    gen_parser.add_argument("--treebanks", help="Comma-separated list of treebank names")
    gen_parser.add_argument("-v", "--verbose", action="store_true", default=True, help="Verbose output")
    gen_parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")
    
    # Validate command
    val_parser = subparsers.add_parser("validate", help="Validate Parquet files against CoNLL-U")
    val_parser.add_argument("--metadata", required=True, help="Path to metadata JSON file")
    val_parser.add_argument("--ud-repos-dir", default="UD_repos", help="Path to UD repositories directory")
    val_parser.add_argument("--parquet-dir", help="Path to parquet directory (implies --local)")
    val_parser.add_argument("--local", action="store_true", help="Validate local files (default parquet dir: 'parquet')")
    val_parser.add_argument("--revision", default="2.17", help="HuggingFace Hub revision (incompatible with --parquet-dir)")
    val_parser.add_argument("--test", action="store_true", help="Test mode: validate 3 treebanks only")
    val_parser.add_argument("--treebanks", help="Comma-separated list of treebank names")
    val_parser.add_argument("-v", "--verbose", action="store_true", default=True, help="Verbose output")
    val_parser.add_argument("-vv", "--very-verbose", action="store_true", help="Show all differences")
    val_parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")

    # Compare command
    cmp_parser = subparsers.add_parser("compare", help="Compare two Parquet outputs")
    cmp_parser.add_argument("--metadata", required=True, help="Path to metadata JSON file")
    cmp_parser.add_argument("--parquet-dir1", required=True, help="First parquet directory")
    cmp_parser.add_argument("--parquet-dir2", required=True, help="Second parquet directory")
    cmp_parser.add_argument("--test", action="store_true", help="Test mode: compare 3 treebanks only")
    cmp_parser.add_argument("--treebanks", help="Comma-separated list of treebank names")
    cmp_parser.add_argument("-v", "--verbose", action="store_true", default=True, help="Verbose output")
    cmp_parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "generate":
        return generate_command(args)
    elif args.command == "validate":
        return validate_command(args)
    elif args.command == "compare":
        return compare_command(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
