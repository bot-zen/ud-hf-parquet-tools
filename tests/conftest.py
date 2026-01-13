#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures.

This file makes the library functions available to all test modules.
"""

import sys
import types

# Make all library functions available for tests
from ud_hf_parquet_tools import (
    conllu_dict_to_string,
    conllu_optional_field,
    example_to_conllu,
    extract_raw_comments_from_sentence,
    extract_raw_fields_from_sentence,
    is_feats_sorted,
    parse_deps,
    parse_feats,
    parse_misc,
    sort_feats_dict,
    write_conllu,
)
from ud_hf_parquet_tools.generator import extract_examples_from_conllu
from ud_hf_parquet_tools.validator import normalize_conllu

# Create a module namespace to match the original test expectations
ud_template = types.ModuleType("ud_template")

# Populate it with all the functions tests expect
ud_template.parse_feats = parse_feats
ud_template.parse_deps = parse_deps
ud_template.parse_misc = parse_misc
ud_template.conllu_dict_to_string = conllu_dict_to_string
ud_template.conllu_optional_field = conllu_optional_field
ud_template.example_to_conllu = example_to_conllu
ud_template.write_conllu = write_conllu
ud_template.normalize_conllu = normalize_conllu

sys.modules["ud_template"] = ud_template

# Create generate_parquet module with functions tests expect
generate_parquet = types.ModuleType("generate_parquet")
generate_parquet.extract_examples_from_conllu = extract_examples_from_conllu
generate_parquet.extract_raw_comments_from_sentence = extract_raw_comments_from_sentence
generate_parquet.extract_raw_fields_from_sentence = extract_raw_fields_from_sentence
generate_parquet.conllu_dict_to_string = conllu_dict_to_string
generate_parquet.conllu_optional_field = conllu_optional_field
generate_parquet.sort_feats_dict = sort_feats_dict
generate_parquet.is_feats_sorted = is_feats_sorted

sys.modules["generate_parquet"] = generate_parquet
