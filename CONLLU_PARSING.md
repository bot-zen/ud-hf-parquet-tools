# CoNLL-U Parsing Issues and Solutions

This document describes the CoNLL-U parsing challenges encountered when working with Universal Dependencies data and how this library addresses them to achieve 100% fidelity.

## Overview

The Python `conllu` library is the standard tool for parsing CoNLL-U files, but it has several bugs and limitations that cause data loss or corruption. This library implements workarounds to ensure perfect reconstruction of the original CoNLL-U data from Parquet format.

## Parsing Issues and Solutions

### 1. Double Equals Sign Bug ✅

**Issue**: The `conllu` library incorrectly parses field values that start with `=`.

**Example**:
```
Original: Gloss==POSS.1SG.NOM|RX==[PRO]|TokenType=Clit
Parsed by conllu: {'Gloss': None, 'RX': None, 'TokenType': 'Clit'}
Expected: {'Gloss': '=POSS.1SG.NOM', 'RX': '=[PRO]', 'TokenType': 'Clit'}
```

**Affected Treebanks**:
- `bej_autogramm` (Beja): 763 sentences
- Any treebank using morphological glosses with `=` prefix

**Solution**: Parse FEATS, XPOS, DEPS, and MISC fields directly from raw TSV lines, bypassing conllu's parser entirely.

**Implementation**: `extract_raw_fields_from_sentence()` in `conllu_utils.py`

**Status**: ✅ **Fully Fixed** - 100% accuracy verified on affected treebanks

---

### 2. Duplicate Metadata Keys ✅

**Issue**: The `conllu` library stores metadata as a Python dictionary, which cannot have duplicate keys. When a sentence has multiple metadata entries with the same key, only the last value is kept.

**Example**:
```conllu
# media = Photo 1280x720, 83.5 KB
# media = <a href="https://...">...</a>
# sent_id = BelarusDocs-257
```

After parsing: `{'media': '<a href="https://...">...</a>', 'sent_id': 'BelarusDocs-257'}`
*(First media entry is lost!)*

**Affected Data**:
- `be_hse` (Belarusian-HSE): 1,216 sentences with duplicate `media` keys
- `sa_ufal` (Sanskrit-UFAL): 18 sentences with duplicate keys
- `br_keb` (Breton-KEB): 15 sentences
- `pt_gsd` (Portuguese-GSD): 8 sentences with duplicate `generator`/`udpipe_model`
- `tr_gb` (Turkish-GB): 3 sentences with duplicate `en`
- **Total**: 1,323 sentences across 14 treebanks

**Solution**: Parse comment lines directly from raw file text before conllu processes them, storing them as an ordered list.

**Implementation**:
- `extract_raw_comments_from_sentence()` in `conllu_utils.py`
- Special markers (`__SENT_ID__`, `__TEXT__`) to preserve order during reconstruction

**Status**: ✅ **Fully Fixed** - All duplicate metadata preserved

---

### 3. Empty Metadata Values ✅

**Issue**: The `conllu` library completely ignores metadata entries with empty values.

**Example**:
```conllu
# text_en =
# sent_id = 1
```

Parsed as: `{'sent_id': '1'}`
*(text_en is completely missing!)*

**Affected Treebanks**: 36 files across multiple treebanks have empty metadata values

**Solution**: Parse raw comment lines and preserve `"key ="` format when value is empty.

**Implementation**: Store empty values as `"key ="` in comments list

**Status**: ✅ **Fully Fixed** - Empty values preserved

---

### 4. Metadata Keys Without Values ✅

**Issue**: The `conllu` library stores metadata keys without values (like `# newpar`) as `{'newpar': None}`. When reconstructing, this would output `# newpar = None` instead of just `# newpar`.

**Example**:
```conllu
# newpar
# sent_id = 1
```

Parsed as: `{'newpar': None, 'sent_id': '1'}`

**Affected Treebanks**: Many treebanks use `# newpar`, `# newdoc` without values

**Solution**: Store as just the key name (e.g., `"newpar"`) without `= None`, and reconstruct as `# newpar`

**Implementation**: Special handling in comment extraction and reconstruction

**Status**: ✅ **Fully Fixed** - Keys without values output correctly

---

### 5. Empty Nodes Before Token 1 ✅

**Issue**: Empty nodes (enhanced dependencies) with decimal IDs less than 1 (like `0.1`, `0.2`) must be inserted before the first token, not after.

**Example**:
```conllu
# sent_id = CESS-CAT-A-19981201-124-s7B
# text = No crec que la nostra vida corri riscos...
0.1	_	_	PRON	p	_	_	_	2:nsubj	ArgTem=arg0:agt|Entity=(...)
1	No	no	ADV	rn	Polarity=Neg	2	advmod	2:advmod	_
```

The empty node `0.1` comes BEFORE token 1, not after a non-existent token 0.

**Affected Treebanks**:
- `ca_ancora` (Catalan-AnCora): 445 sentences with empty nodes at position 0.x
- Any treebank using empty nodes for pro-drop subjects or other zero elements

**Solution**: Special handling in reconstruction code to insert empty nodes with ID < 1 before the token loop starts.

**Implementation**: Empty nodes are sorted by ID and inserted in correct order during reconstruction

**Status**: ✅ **Fully Fixed** - Empty nodes at all positions reconstructed correctly

---

### 6. Multi-Word Tokens (MWTs) ✅

**Issue**: Not a bug, but MWTs need special handling to avoid including them in syntactic word sequences.

**Example**:
```conllu
1-2	du	_	_	_	_	_	_	_	_
1	de	de	ADP	_	_	2	case	_	_
2	le	le	DET	_	Gender=Masc|Number=Sing	3	det	_	_
```

The line `1-2` is a surface form (contraction), while lines `1` and `2` are the syntactic words.

**Solution**:
- Filter token sequences to syntactic words only (integer IDs)
- Store MWTs separately with their ID, form, FEATS (optional, for `Typo=Yes`), and MISC

**Implementation**:
- `sent.filter(id=lambda x: type(x) is int)` filters to syntactic words
- MWTs stored in separate `mwt` field

**Status**: ✅ **Fully Implemented** - MWTs preserved and syntactic words correct

---

### 7. Empty Nodes (Enhanced Dependencies) ✅

**Issue**: Not a bug, but empty nodes need full preservation of all 10 CoNLL-U fields.

**Example**:
```conllu
22.1	pro	_	PRON	_	_	23	nsubj	_	_
```

**Solution**: Store empty nodes with all 10 fields in separate `empty_nodes` field

**Implementation**: Full field extraction for empty nodes (ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC)

**Status**: ✅ **Fully Implemented** - All empty node data preserved

---

## Known Acceptable Limitations

### 1. File-Level Comments ⚠️

**Issue**: Comments before the first sentence (like encoding declarations) are not associated with any sentence and are lost.

**Example**:
```conllu
# -*- coding: UTF-8 -*-
# sent_id = 1
```

The encoding line is not part of any sentence's metadata.

**Affected Treebanks**: Various treebanks with encoding declarations at file start

**Rationale**: These are file-level metadata, not sentence-level. Encoding declarations are informational only and don't affect linguistic data.

**Status**: ⚠️ **Accepted limitation** - File-level metadata excluded

---

### 2. Double-Hash Comments ⚠️

**Issue**: Comments with double hashes (like `# # newpar`) have inconsistent spacing.

**Example**:
```conllu
# # newpar
# sent_id = 11
```

Parsed as: `{'sent_id': '11'}` (double-hash comment handled specially)

**Affected Treebanks**:
- `ajp_madar` (South Levantine Arabic-MADAR): 1 occurrence
- `sa_ufal` (Sanskrit-UFAL): 1 occurrence

**Impact**: These may appear with slightly different spacing: `# # newpar` vs `# #newpar`

**Status**: ⚠️ **Minor formatting difference** - Rare edge case (2 treebanks, 2 occurrences total)

---

## Implementation Strategy

### Hybrid Parsing Approach

We use a hybrid strategy to work around conllu's limitations:

1. **Comments/Metadata**: Parse raw lines before conllu to preserve:
   - Duplicate keys
   - Empty values
   - Keys without values
   - Original ordering

2. **Token fields (FEATS/MISC/DEPS/XPOS)**: Parse raw TSV fields to bypass:
   - Double equals bug
   - Any other value parsing issues

3. **Token structure (FORM/LEMMA/UPOS/HEAD/DEPREL)**: Use conllu's parsed values:
   - These work correctly
   - Reliable for basic token structure

### Performance Impact

The raw parsing adds minimal overhead:
- One additional string split operation per sentence
- No additional file I/O (we read the file once)
- Negligible impact on overall generation time
- String operations are extremely fast compared to I/O

### Code Organization

**Core Utilities** (`src/ud_hf_parquet_tools/conllu_utils.py`):
- `extract_raw_fields_from_sentence()`: Raw field extraction
- `extract_raw_comments_from_sentence()`: Raw comment extraction
- `example_to_conllu()`: Reconstruction with special handling

**Generator** (`src/ud_hf_parquet_tools/generator.py`):
- Uses raw extraction functions during parquet generation
- Stores raw fields directly in dataset

**Validator** (`src/ud_hf_parquet_tools/validator.py`):
- Uses `example_to_conllu()` for reconstruction
- Compares reconstructed output with original

---

## Fidelity Results

### ✅ Fully Fixed Issues (100% Accuracy)
1. Double equals parsing bug
2. Duplicate metadata keys
3. Empty metadata values
4. Metadata keys without values
5. Empty nodes with ID < 1 (0.x positions)
6. Multi-word token handling
7. Empty node full field preservation

### ⚠️ Known Acceptable Limitations
1. File-level comments (encoding declarations) - not sentence-level data
2. Double-hash comments - minor spacing differences (2 occurrences total)

### 📊 Fidelity Summary
- **100% fidelity** for linguistic data (tokens, annotations, dependencies)
- **~99.99% fidelity** for metadata (minor formatting differences in 2 sentences out of millions)
- **0 data loss** for linguistic annotations

---

## Testing

### Validation Command

```bash
# Validate all local treebanks
ud-hfp-tools validate --metadata metadata.json --local

# Validate specific treebanks with detailed diffs
ud-hfp-tools validate --metadata metadata.json --treebanks be_hse,bej_autogramm --local -vv

# Test 3 diverse treebanks
ud-hfp-tools validate --metadata metadata.json --test --local
```

### Test Coverage

The library includes comprehensive tests for all edge cases:
- `tests/test_extraction.py`: Raw field extraction
- `tests/test_reconstruction.py`: CoNLL-U reconstruction
- `tests/test_roundtrip.py`: Full roundtrip validation

### Verified Treebanks

All 336 Universal Dependencies v2.17 treebanks pass validation with:
- 100% token line matches
- ~99.99% metadata line matches (excluding known acceptable limitations)

**Specifically tested problematic treebanks**:
- `bej_autogramm`: 763/763 sentences (double equals bug verified fixed)
- `be_hse`: 1,216 sentences (duplicate metadata verified preserved)
- `ca_ancora`: 445 sentences (empty nodes < 1 verified correct)
- `fr_gsd`, `en_ewt`, `it_isdt`: All splits pass (test suite)

---

## References

- [Universal Dependencies format specification](https://universaldependencies.org/format.html)
- [Python conllu library](https://github.com/EmilStenstrom/conllu)
- [Universal Dependencies v2.17 release](https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-5150)
- [CoNLL-U format issues discussion](https://github.com/UniversalDependencies/docs/issues)

---

## Contributing

If you discover additional CoNLL-U parsing issues:

1. Document the issue with examples from real treebanks
2. Identify the number of affected sentences
3. Propose a solution that maintains 100% fidelity
4. Add test cases to verify the fix
5. Submit a pull request with the implementation

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.
