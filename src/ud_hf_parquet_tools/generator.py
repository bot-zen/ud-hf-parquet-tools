"""
Parquet generation module for Universal Dependencies datasets.

This module converts CoNLL-U files from UD repositories into Parquet format
for efficient loading with HuggingFace datasets.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

import conllu
import datasets

from .conllu_utils import (
    conllu_dict_to_string,
    conllu_optional_field,
    extract_raw_comments_from_sentence,
    extract_raw_fields_from_sentence,
)


def extract_examples_from_conllu(filepath: str) -> List[Dict[str, Any]]:
    """
    Extract examples from a CoNLL-U file with MWT and empty node support.

    Args:
        filepath: Path to the CoNLL-U file

    Returns:
        List of example dictionaries matching the dataset schema
    """
    examples = []

    # Read raw file to extract comments before conllu parsing
    with open(filepath, "r", encoding="utf-8") as f:
        file_content = f.read()

    # Split into sentence blocks
    sentence_blocks = file_content.split("\n\n")

    # Parse with conllu
    with open(filepath, "r", encoding="utf-8") as data_file:
        tokenlist = list(conllu.parse_incr(data_file))

        for idx, sent in enumerate(tokenlist):
            # Get raw comments and fields from original text
            if idx < len(sentence_blocks):
                comments, sent_id, text = extract_raw_comments_from_sentence(sentence_blocks[idx])
                raw_fields = extract_raw_fields_from_sentence(sentence_blocks[idx])
            else:
                comments = []
                sent_id = None
                text = None
                raw_fields = {}

            # Fallback to conllu metadata if needed
            if sent_id is None and "sent_id" in sent.metadata:
                sent_id = sent.metadata["sent_id"]
            if sent_id is None:
                sent_id = str(idx)

            if text is None and "text" in sent.metadata:
                text = sent.metadata["text"]

            # Note: comments and raw fields are now extracted from raw file above,
            # preserving duplicates and bypassing conllu parsing bugs

            # Extract Multi-Word Tokens (MWTs) - tokens with tuple IDs like (1, '-', 2)
            # Note: Exclude empty nodes which have '.' as middle element: (22, '.', 1)
            # Per UD spec: MWTs can have ID, FORM, MISC, and optionally FEATS (for "Typo=Yes")
            mwts = []
            for token in sent:
                if isinstance(token["id"], tuple) and len(token["id"]) == 3 and token["id"][1] == "-":
                    # MWT line (e.g., (1, '-', 2) for "1-2")
                    mwt_id = f"{token['id'][0]}-{token['id'][2]}"

                    # Use raw fields if available (bypasses conllu parsing bugs)
                    if mwt_id in raw_fields:
                        feats = raw_fields[mwt_id]["feats"]
                        misc = raw_fields[mwt_id]["misc"]
                    else:
                        # Fallback to conllu parsed values
                        feats = conllu_optional_field(token["feats"], "MWT.FEATS", sent_id, is_feats=True)
                        misc = conllu_optional_field(token["misc"], "MWT.MISC", sent_id)

                    mwts.append({"id": mwt_id, "form": token["form"], "feats": feats, "misc": misc})

            # Extract Empty Nodes - tokens with decimal IDs like 22.1
            # These are represented as tuples: (22, '.', 1)
            empty_nodes = []
            for token in sent:
                if isinstance(token["id"], tuple) and len(token["id"]) == 3 and token["id"][1] == ".":
                    # Empty node (e.g., (22, '.', 1) for ID "22.1")
                    empty_node_id = f"{token['id'][0]}.{token['id'][2]}"

                    # Use raw fields if available (bypasses conllu parsing bugs)
                    if empty_node_id in raw_fields:
                        xpos = raw_fields[empty_node_id]["xpos"]
                        feats = raw_fields[empty_node_id]["feats"]
                        deps = raw_fields[empty_node_id]["deps"]
                        misc = raw_fields[empty_node_id]["misc"]
                    else:
                        # Fallback to conllu parsed values
                        xpos = token["xpos"] or None
                        feats = conllu_dict_to_string(
                            token["feats"], "FEATS", f"{sent_id}:{empty_node_id}", is_feats=True
                        )
                        deps = conllu_dict_to_string(token["deps"], "DEPS", f"{sent_id}:{empty_node_id}")
                        misc = conllu_dict_to_string(token["misc"], "MISC", f"{sent_id}:{empty_node_id}")

                    empty_nodes.append(
                        {
                            "id": empty_node_id,
                            "form": token["form"],
                            "lemma": token["lemma"] or "_",
                            "upos": token["upos"] or "_",
                            "xpos": xpos or "_",
                            "feats": feats,
                            "head": str(token["head"]) if token["head"] is not None else "_",
                            "deprel": str(token["deprel"]) if token["deprel"] else "_",
                            "deps": deps,
                            "misc": misc,
                        }
                    )

            # Filter to syntactic words only (exclude MWTs and empty nodes)
            sent_filtered = sent.filter(id=lambda x: type(x) is int)

            # Extract token fields from syntactic words
            tokens = [token["form"] for token in sent_filtered]

            # If text wasn't in metadata, reconstruct from tokens
            if text is None:
                text = " ".join(tokens)

            # Extract fields for regular tokens, using raw fields when available
            xpos_list = []
            feats_list = []
            deps_list = []
            misc_list = []

            for token in sent_filtered:
                token_id = str(token["id"])

                # Use raw fields if available (bypasses conllu parsing bugs)
                if token_id in raw_fields:
                    xpos_list.append(raw_fields[token_id]["xpos"])
                    feats_list.append(raw_fields[token_id]["feats"])
                    deps_list.append(raw_fields[token_id]["deps"])
                    misc_list.append(raw_fields[token_id]["misc"])
                else:
                    # Fallback to conllu parsed values
                    xpos_list.append(conllu_optional_field(token["xpos"], "XPOS", sent_id))
                    feats_list.append(conllu_optional_field(token["feats"], "FEATS", sent_id, is_feats=True))
                    deps_list.append(conllu_optional_field(token["deps"], "DEPS", sent_id))
                    misc_list.append(conllu_optional_field(token["misc"], "MISC", sent_id))

            # Create example with proper types per UD specification:
            # - Required fields (FORM, LEMMA, UPOS, HEAD, DEPREL): always string
            # - Optional fields (XPOS, FEATS, DEPS, MISC): None when unspecified
            example = {
                "sent_id": sent_id,
                "text": text,
                "comments": comments,
                "tokens": tokens,
                "lemmas": [token["lemma"] for token in sent_filtered],
                "upos": [token["upos"] for token in sent_filtered],
                "xpos": xpos_list,
                "feats": feats_list,
                "head": [str(token["head"]) if token["head"] is not None else "_" for token in sent_filtered],
                "deprel": [str(token["deprel"]) if token["deprel"] else "_" for token in sent_filtered],
                "deps": deps_list,
                "misc": misc_list,
                "mwt": mwts,
                "empty_nodes": empty_nodes,
            }

            examples.append(example)

    return examples


def generate_parquet_for_treebank(
    name: str,
    metadata: Dict[str, Any],
    ud_repos_dir: Path,
    output_dir: Path,
    verbose: bool = True,
    overwrite: bool = False,
) -> bool:
    """
    Generate Parquet files for a single treebank.

    Args:
        name: Treebank name (e.g., "fr_gsd")
        metadata: Treebank metadata including splits and file paths
        ud_repos_dir: Path to UD_repos directory containing treebank data
        output_dir: Output directory for Parquet files
        verbose: Print progress messages
        overwrite: Overwrite existing parquet files (default: skip existing)

    Returns:
        True if successful, False otherwise
    """
    # Create output directory for this treebank
    treebank_output_dir = output_dir / name
    treebank_output_dir.mkdir(parents=True, exist_ok=True)

    # Check if all parquet files already exist
    if not overwrite:
        expected_files = []
        for split_name in metadata.get("splits", {}).keys():
            parquet_path = treebank_output_dir / f"{split_name}.parquet"
            expected_files.append((split_name, parquet_path))

        all_exist = all(path.exists() for _, path in expected_files)

        if all_exist and expected_files:
            if verbose:
                print(f"Skipping {name} (all parquet files exist, use --overwrite to regenerate)")
            return True

    if verbose:
        print(f"Processing {name}...")

    # Process each split
    dataset_dict = {}

    for split_name, split_data in metadata.get("splits", {}).items():
        files = split_data.get("files", [])
        if not files:
            continue

        if verbose:
            print(f"  - {split_name}: {len(files)} file(s)")

        # Extract examples from all files in this split
        all_examples = []
        for file_path in files:
            # Extract just the filename from the path (metadata includes dirname/revision/filename)
            # e.g., "UD_French-GSD/r2.17/fr_gsd-ud-train.conllu" -> "fr_gsd-ud-train.conllu"
            filename = Path(file_path).name

            # Construct full path: UD_repos/dirname/filename
            full_path = ud_repos_dir / metadata["dirname"] / filename

            if not full_path.exists():
                print(f"    Warning: File not found: {full_path}", file=sys.stderr)
                continue

            try:
                examples = extract_examples_from_conllu(str(full_path))
                all_examples.extend(examples)
            except Exception as e:
                print(f"    Error processing {full_path}: {e}", file=sys.stderr)
                return False

        if not all_examples:
            print(f"    Warning: No examples extracted for {split_name}", file=sys.stderr)
            continue

        # Define features
        features = datasets.Features(
            {
                "sent_id": datasets.Value("string"),
                "text": datasets.Value("string"),
                "comments": datasets.Sequence(datasets.Value("string")),
                "tokens": datasets.Sequence(datasets.Value("string")),
                "lemmas": datasets.Sequence(datasets.Value("string")),
                "upos": datasets.Sequence(
                    datasets.features.ClassLabel(
                        names=[
                            "NOUN",
                            "PUNCT",
                            "ADP",
                            "NUM",
                            "SYM",
                            "SCONJ",
                            "ADJ",
                            "PART",
                            "DET",
                            "CCONJ",
                            "PROPN",
                            "PRON",
                            "X",
                            "_",
                            "ADV",
                            "INTJ",
                            "VERB",
                            "AUX",
                        ]
                    )
                ),
                "xpos": datasets.Sequence(datasets.Value("string")),
                "feats": datasets.Sequence(datasets.Value("string")),
                "head": datasets.Sequence(datasets.Value("string")),
                "deprel": datasets.Sequence(datasets.Value("string")),
                "deps": datasets.Sequence(datasets.Value("string")),
                "misc": datasets.Sequence(datasets.Value("string")),
                "mwt": [
                    {
                        "id": datasets.Value("string"),
                        "form": datasets.Value("string"),
                        "feats": datasets.Value("string"),
                        "misc": datasets.Value("string"),
                    }
                ],
                "empty_nodes": [
                    {
                        "id": datasets.Value("string"),
                        "form": datasets.Value("string"),
                        "lemma": datasets.Value("string"),
                        "upos": datasets.Value("string"),
                        "xpos": datasets.Value("string"),
                        "feats": datasets.Value("string"),
                        "head": datasets.Value("string"),
                        "deprel": datasets.Value("string"),
                        "deps": datasets.Value("string"),
                        "misc": datasets.Value("string"),
                    }
                ],
            }
        )

        # Create dataset from examples
        dataset = datasets.Dataset.from_list(all_examples, features=features)
        dataset_dict[split_name] = dataset

        if verbose:
            print(f"    Created dataset with {len(dataset)} examples")

    if not dataset_dict:
        print(f"  Warning: No splits processed for {name}", file=sys.stderr)
        return False

    # Create DatasetDict and save to Parquet
    dataset_dict_obj = datasets.DatasetDict(dataset_dict)

    try:
        # Save as Parquet files
        for split_name, dataset in dataset_dict_obj.items():
            parquet_path = treebank_output_dir / f"{split_name}.parquet"
            dataset.to_parquet(parquet_path)
            if verbose:
                print(f"    Saved {split_name}.parquet ({parquet_path.stat().st_size / 1024 / 1024:.2f} MB)")

        return True

    except Exception as e:
        print(f"  Error saving Parquet files: {e}", file=sys.stderr)
        return False
