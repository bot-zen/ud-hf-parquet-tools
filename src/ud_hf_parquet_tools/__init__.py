"""
UD-HF-Parquet-Tools: Tools for generating and validating Universal Dependencies Parquet datasets.

This library provides both a Python API and CLI for converting Universal Dependencies
CoNLL-U data to Parquet format and validating the conversion.
"""

__version__ = "1.3.0"
__author__ = "Egon W. Stemle"
__email__ = "egon.stemle@eurac.edu"

from .conllu_utils import (
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
from .comment_materialization import materialize_comment_markers_batch
from .generator import generate_parquet_for_treebank
from .validator import normalize_conllu, validate_treebank, validate_treebank_text

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    # Generator
    "generate_parquet_for_treebank",
    # Validator
    "validate_treebank",
    "validate_treebank_text",
    "normalize_conllu",
    # CoNLL-U utilities
    "conllu_dict_to_string",
    "conllu_optional_field",
    "example_to_conllu",
    "extract_raw_comments_from_sentence",
    "extract_raw_fields_from_sentence",
    "is_feats_sorted",
    "parse_deps",
    "parse_feats",
    "parse_misc",
    "sort_feats_dict",
    "write_conllu",
    "materialize_comment_markers_batch",
]
