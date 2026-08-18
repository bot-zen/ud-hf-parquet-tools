"""
CoNLL-U utilities for parsing and converting Universal Dependencies data.

This module provides utilities for handling CoNLL-U format with full fidelity,
including edge cases like double equals, duplicate metadata, empty nodes, and MWTs.
"""

import warnings
from collections import OrderedDict
from typing import Any, Dict, List, Tuple

# Warning counters
MALFORMED_FEATS_COUNT = 0
UNSORTED_FEATS_COUNT = 0


def sort_feats_dict(feats_dict: Dict[str, str]) -> Dict[str, str]:
    """
    Sort FEATS dictionary alphabetically by keys (case-insensitive) per UD spec.

    Also sorts values if they contain multiple comma-separated values.

    Args:
        feats_dict: Dictionary of feature name -> value

    Returns:
        Sorted dictionary (OrderedDict preserving sorted order)
    """
    sorted_dict = OrderedDict()

    # Sort keys case-insensitively
    for key in sorted(feats_dict.keys(), key=str.lower):
        value = feats_dict[key]

        # If value contains comma-separated items, sort them too
        if "," in value:
            value_parts = [v.strip() for v in value.split(",")]
            value = ",".join(sorted(value_parts, key=str.lower))

        sorted_dict[key] = value

    return sorted_dict


def is_feats_sorted(feats_dict: Dict[str, str]) -> bool:
    """Check if FEATS dictionary is sorted per UD spec."""
    keys = list(feats_dict.keys())
    sorted_keys = sorted(keys, key=str.lower)

    if keys != sorted_keys:
        return False

    # Check if values with commas are sorted
    for value in feats_dict.values():
        if "," in value:
            value_parts = [v.strip() for v in value.split(",")]
            sorted_parts = sorted(value_parts, key=str.lower)
            if value_parts != sorted_parts:
                return False

    return True


def conllu_dict_to_string(value: Any, field_name: str = "", sent_id: str = "", is_feats: bool = False) -> str:
    """
    Convert CoNLL-U field value to standard CoNLL-U string format.

    Args:
        value: Field value (dict, OrderedDict, list, string, or None)
        field_name: Name of the field (for warnings)
        sent_id: Sentence ID (for warnings)
        is_feats: True if this is a FEATS field (will check sorting per UD spec)

    Returns:
        CoNLL-U format string ("Key=Val|Key2=Val2" or "_")
    """
    global MALFORMED_FEATS_COUNT, UNSORTED_FEATS_COUNT

    if value is None:
        return "_"

    if isinstance(value, dict):
        if not value:
            return "_"

        # For FEATS fields, check if sorted per UD spec (but don't auto-correct)
        if is_feats:
            if not is_feats_sorted(value):
                UNSORTED_FEATS_COUNT += 1
                if UNSORTED_FEATS_COUNT <= 10:
                    orig_str = "|".join([f"{k}={v}" for k, v in value.items()])
                    warnings.warn(f"FEATS field not sorted per UD spec in {sent_id}: {orig_str}", UserWarning)

        # Convert dict to CoNLL-U format: Key=Value|Key2=Value2
        items = []
        for k, v in value.items():
            if v is None or v == "":
                MALFORMED_FEATS_COUNT += 1
                if MALFORMED_FEATS_COUNT <= 10:
                    warnings.warn(f"Malformed {field_name} entry in {sent_id}: '{k}' without '=Value'", UserWarning)
                items.append(k)
            else:
                items.append(f"{k}={v}")
        return "|".join(items)

    if isinstance(value, list):
        if not value:
            return "_"
        # Convert list of tuples to CoNLL-U DEPS format: head:rel|head2:rel2
        items = []
        for rel, head in value:
            if isinstance(head, tuple) and len(head) == 3:
                # Empty node reference: (21, '.', 1) -> "21.1"
                head_str = f"{head[0]}.{head[2]}"
            else:
                head_str = str(head)
            items.append(f"{head_str}:{rel}")
        return "|".join(items)

    # Already a string
    s = str(value)
    if s == "None":
        return "_"
    return s


def conllu_optional_field(value: Any, field_name: str = "", sent_id: str = "", is_feats: bool = False) -> str | None:
    """
    Convert CoNLL-U optional field value to Python representation.
    Returns None for unspecified values (_), proper format otherwise.

    Use for: XPOS, FEATS, DEPS, MISC (optional fields per UD spec)

    Args:
        value: Field value (dict, OrderedDict, list, string, or None)
        field_name: Name of the field (for warnings)
        sent_id: Sentence ID (for warnings)
        is_feats: True if this is a FEATS field

    Returns:
        None for unspecified, or CoNLL-U format string
    """
    global MALFORMED_FEATS_COUNT, UNSORTED_FEATS_COUNT

    if value is None:
        return None

    if isinstance(value, dict):
        if not value:
            return None

        if is_feats:
            if not is_feats_sorted(value):
                UNSORTED_FEATS_COUNT += 1
                if UNSORTED_FEATS_COUNT <= 10:
                    orig_str = "|".join([f"{k}={v}" for k, v in value.items()])
                    warnings.warn(f"FEATS field not sorted per UD spec in {sent_id}: {orig_str}", UserWarning)

        items = []
        for k, v in value.items():
            if v is None or v == "":
                MALFORMED_FEATS_COUNT += 1
                if MALFORMED_FEATS_COUNT <= 10:
                    warnings.warn(f"Malformed {field_name} entry in {sent_id}: '{k}' without '=Value'", UserWarning)
                items.append(k)
            else:
                items.append(f"{k}={v}")
        return "|".join(items)

    if isinstance(value, list):
        if not value:
            return None
        items = []
        for rel, head in value:
            if isinstance(head, tuple) and len(head) == 3:
                head_str = f"{head[0]}.{head[2]}"
            else:
                head_str = str(head)
            items.append(f"{head_str}:{rel}")
        return "|".join(items)

    s = str(value)
    if s == "None" or s == "_" or s == "":
        return None
    return s


def extract_raw_fields_from_sentence(sentence_text: str) -> Dict[str, Dict[str, str | None]]:
    """
    Extract raw FEATS, XPOS, DEPS, and MISC fields directly from token lines.

    This bypasses the conllu library's parsing which has bugs with double equals (==).

    Returns:
        Dict mapping token_id -> {'feats': str, 'xpos': str, 'deps': str, 'misc': str}
    """
    raw_fields = {}

    for line in sentence_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        fields = line.split("\t")
        if len(fields) < 10:
            continue

        token_id = fields[0]
        xpos = fields[4] if fields[4] != "_" else None
        feats = fields[5] if fields[5] != "_" else None
        deps = fields[8] if fields[8] != "_" else None
        misc = fields[9] if fields[9] != "_" else None

        raw_fields[token_id] = {"xpos": xpos, "feats": feats, "deps": deps, "misc": misc}

    return raw_fields


def extract_raw_comments_from_sentence(sentence_text: str) -> Tuple[List[str], str | None, str | None]:
    """
    Extract raw comment lines from a sentence before conllu parsing.

    This preserves metadata that conllu's dictionary-based storage loses:
    - Duplicate metadata keys
    - Keys without values
    - Empty values

    Returns:
        (comments_list, sent_id, text) where comments_list preserves all comments
    """
    comments = []
    sent_id = None
    text = None

    for line in sentence_text.split("\n"):
        line = line.strip()
        if not line.startswith("#"):
            continue

        comment_content = line[1:].strip()

        if not comment_content:
            continue

        if " = " in comment_content:
            key, value = comment_content.split(" = ", 1)
            key = key.strip()
            value = value.strip()

            if key == "sent_id":
                sent_id = value
                comments.append("__SENT_ID__")
            elif key == "text":
                text = value
                comments.append("__TEXT__")
            else:
                if value:
                    comments.append(f"{key} = {value}")
                else:
                    comments.append(f"{key} =")
        else:
            comments.append(comment_content)

    return comments, sent_id, text


def example_to_conllu(example: Dict[str, Any], upos_names: List[str] | None = None) -> str:
    """
    Convert a dataset example back to CoNLL-U format.

    Args:
        example: Dataset example with all fields
        upos_names: Optional list of UPOS label names for ClassLabel conversion

    Returns:
        CoNLL-U formatted string for this sentence
    """
    lines = []

    # Track if we've added sent_id and text via markers
    sent_id_added = False
    text_added = False

    # Reconstruct comments in original order using markers
    for comment in example.get("comments", []):
        if comment == "__SENT_ID__":
            # Insert sent_id at its original position
            if "sent_id" in example and example["sent_id"]:
                lines.append(f"# sent_id = {example['sent_id']}")
                sent_id_added = True
        elif comment == "__TEXT__":
            # Insert text at its original position
            if "text" in example and example["text"]:
                lines.append(f"# text = {example['text']}")
                text_added = True
        else:
            # Regular comment
            lines.append(f"# {comment}")

    # Fallback: if sent_id/text exist but weren't added via markers, add them now
    # This handles cases where comments list is empty or missing markers
    if not sent_id_added and "sent_id" in example and example["sent_id"]:
        lines.append(f"# sent_id = {example['sent_id']}")
    if not text_added and "text" in example and example["text"]:
        lines.append(f"# text = {example['text']}")

    # Parse MWT ranges
    mwt_ranges = {}
    for mwt in example.get("mwt", []):
        mwt_id = mwt["id"]
        if "-" in mwt_id:
            start, _ = mwt_id.split("-")
            mwt_ranges[int(start)] = mwt

    # Parse empty node positions
    empty_node_positions = {}
    for empty_node in example.get("empty_nodes", []):
        en_id = empty_node["id"]
        if "." in en_id:
            parent, _ = en_id.split(".")
            if int(parent) not in empty_node_positions:
                empty_node_positions[int(parent)] = []
            empty_node_positions[int(parent)].append(empty_node)

    # Insert empty nodes before token 1 (e.g., 0.1, 0.2)
    if 0 in empty_node_positions:
        for empty_node in empty_node_positions[0]:
            en_fields = [
                empty_node.get("id", "_"),
                empty_node.get("form", "_"),
                empty_node.get("lemma", "_"),
                empty_node.get("upos", "_"),
                empty_node.get("xpos") or "_",
                empty_node.get("feats") or "_",
                empty_node.get("head", "_"),
                empty_node.get("deprel", "_"),
                empty_node.get("deps") or "_",
                empty_node.get("misc") or "_",
            ]
            lines.append("\t".join(en_fields))

    # Build token lines with MWTs and empty nodes
    token_idx = 1
    for i in range(len(example["tokens"])):
        # Insert MWT line if needed
        if token_idx in mwt_ranges:
            mwt = mwt_ranges[token_idx]
            feats = mwt.get("feats") or "_"
            misc = mwt.get("misc") or "_"
            lines.append(f"{mwt['id']}\t{mwt['form']}\t_\t_\t_\t{feats}\t_\t_\t_\t{misc}")

        # Convert UPOS from ClassLabel index to string if needed
        upos_value = example["upos"][i]
        if isinstance(upos_value, int) and upos_names:
            upos_str = upos_names[upos_value]
        else:
            upos_str = str(upos_value)

        # Regular token line
        fields = [
            str(token_idx),
            str(example["tokens"][i]),
            str(example["lemmas"][i]),
            str(upos_str),
            str(example["xpos"][i] or "_"),
            str(example["feats"][i] or "_"),
            str(example["head"][i]),
            str(example["deprel"][i]),
            str(example["deps"][i] or "_"),
            str(example["misc"][i] or "_"),
        ]
        lines.append("\t".join(fields))

        # Insert empty nodes after token if needed
        if token_idx in empty_node_positions:
            for empty_node in empty_node_positions[token_idx]:
                en_fields = [
                    empty_node.get("id", "_"),
                    empty_node.get("form", "_"),
                    empty_node.get("lemma", "_"),
                    empty_node.get("upos", "_"),
                    empty_node.get("xpos") or "_",
                    empty_node.get("feats") or "_",
                    empty_node.get("head", "_"),
                    empty_node.get("deprel", "_"),
                    empty_node.get("deps") or "_",
                    empty_node.get("misc") or "_",
                ]
                lines.append("\t".join(en_fields))

        token_idx += 1

    return "\n".join(lines) + "\n\n"


def parse_feats(feats_str: str | None) -> Dict[str, str]:
    """
    Parse CoNLL-U FEATS field string to dictionary.

    Args:
        feats_str: CoNLL-U format string like "Case=Nom|Number=Sing" or None

    Returns:
        Dictionary mapping feature names to values, empty dict if None

    Raises:
        ValueError: If feats_str is empty string
    """
    if feats_str is None or feats_str == "_":
        return {}
    if feats_str == "":
        raise ValueError("Cannot parse empty string")
    return dict(kv.split("=", 1) for kv in feats_str.split("|") if "=" in kv)


def parse_deps(deps_str: str | None) -> Dict[str, str]:
    """
    Parse CoNLL-U DEPS field string to dictionary.

    Args:
        deps_str: CoNLL-U enhanced dependencies format like "4:nsubj|6:nsubj" or None

    Returns:
        Dictionary mapping head indices to dependency relations, empty dict if None

    Raises:
        ValueError: If deps_str is empty string
    """
    if deps_str is None or deps_str == "_":
        return {}
    if deps_str == "":
        raise ValueError("Cannot parse empty string")
    return dict(kv.split(":", 1) for kv in deps_str.split("|"))


def parse_misc(misc_str: str | None) -> Dict[str, str]:
    """
    Parse CoNLL-U MISC field string to dictionary.

    Args:
        misc_str: CoNLL-U format string like "SpaceAfter=No|Translit=value" or None

    Returns:
        Dictionary mapping misc keys to values, empty dict if None

    Raises:
        ValueError: If misc_str is empty string
    """
    if misc_str is None or misc_str == "_":
        return {}
    if misc_str == "":
        raise ValueError("Cannot parse empty string")
    return dict(kv.split("=", 1) for kv in misc_str.split("|") if "=" in kv)


def write_conllu(dataset, output_file=None, upos_names=None):
    """
    Write a dataset to CoNLL-U format.

    Args:
        dataset: HuggingFace dataset with UD examples
        output_file: Output file path, None for file-like object, "-" for stdout
        upos_names: Optional list of UPOS label names for ClassLabel conversion

    Returns:
        StringIO object if output_file is None, otherwise None
    """
    from io import StringIO
    import sys

    # Get upos_names from dataset features if not provided. New outputs store
    # UPOS strings directly; this remains for old ClassLabel parquet outputs.
    if upos_names is None and hasattr(dataset, "features"):
        upos_feature = dataset.features.get("upos", None)
        inner_feature = getattr(upos_feature, "feature", None)
        upos_names = getattr(inner_feature, "names", None)

    # Determine output target
    if output_file is None:
        output = StringIO()
        return_buffer = True
        close_file = False
    elif output_file == "-":
        output = sys.stdout
        return_buffer = False
        close_file = False
    elif isinstance(output_file, str):
        output = open(output_file, "w", encoding="utf-8")
        return_buffer = False
        close_file = True
    else:
        output = output_file
        return_buffer = False
        close_file = False

    try:
        # Write each example as CoNLL-U
        for example in dataset:
            conllu_text = example_to_conllu(example, upos_names)
            output.write(conllu_text)

        # Return StringIO buffer if requested
        if return_buffer:
            return output
    finally:
        # Close file if we opened it
        if close_file:
            output.close()
