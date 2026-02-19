# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Make generated Parquet outputs reproducible by sorting split/file processing order
  and using stable `to_parquet` write settings (fixed batch size, CDC/page-index disabled).

## [1.2.0] - 2026-02-12

### Added
- DuckDB-backed batch comment materialization API: `materialize_comment_markers_batch`
- New dependency: `duckdb>=1.1.0`
- Documentation:
  - README.md TestPyPI badge

### Changed
- Exposed comment materialization helper in public package exports
- Added tests for marker replacement, passthrough behavior, and order preservation

### Fixed
- DuckDB Arrow compatibility: handle both `pyarrow.Table` and
  `pyarrow.RecordBatchReader` outputs when converting query results

## [1.1.0] - 2025-01-13

### Added
- **CONLLU_PARSING.md**: Comprehensive documentation of CoNLL-U parsing issues
  - All 7 parsing challenges with real treebank examples
  - Affected treebank statistics (1,323+ sentences with issues)
  - Implementation strategies and code locations
  - Testing procedures and fidelity results
- **RELEASE.md**: Complete release process documentation
  - Pre-release checklist
  - Version numbering guidelines
  - Git tagging and PyPI publishing workflow with uv
  - Troubleshooting guide
- **CHANGELOG.md**: Version history following Keep a Changelog format
- `compare` command: Compare two parquet outputs using PyArrow table comparison
- `--overwrite` flag: Skip regeneration of existing parquet files by default
- `--blocked-treebanks` flag: Filter treebanks with license restrictions

### Changed
- **Migration to uv**: Use native `uv build` and `uv publish` commands
  - Removed dependency on separate build and twine packages
  - Updated all documentation and examples to use uv
  - Authentication via UV_PUBLISH_TOKEN or system keyring
- **pyproject.toml**: Align with uv dependency groups standard
  - Changed `[project.optional-dependencies]` to `[dependency-groups]`
  - Updated pytest from >=7.0.0 to >=9.0.2
- **CLI improvements**:
  - `--parquet-dir` now implies `--local` and is incompatible with `--revision`
  - Distinguish between metadata and token line errors in validation output
  - Skip diff header lines (---, +++, @@) in error counting
- Applied ruff formatting and linting across codebase
- Finalized CLI command name as `ud-hfp-tools`

### Fixed
- Metadata order preservation in CoNLL-U reconstruction
  - Special markers (__SENT_ID__, __TEXT__) preserve original ordering
  - Fallback handling when comments list is empty
- Validator properly reports missing CoNLL-U files instead of confusing diffs
- TypeError when using HuggingFace Hub string paths (not Path objects)
- `--revision` flag now correctly constructs HF Hub paths

### Removed
- `examples/` directory (functionality fully covered by CLI and wrapper scripts)

## [1.0.0] - 2025-01-13

### Added
- Initial public release
- Core parquet generation from CoNLL-U files
- Multi-Word Token (MWT) support with structured data
- Empty node support
- Validation against original CoNLL-U data
- Comparison between two parquet outputs
- CLI tool (`ud-hfp-tools`) with three commands:
  - `generate`: Create parquet files from UD repositories
  - `validate`: Verify parquet files match CoNLL-U source
  - `compare`: Compare two parquet outputs
- Support for blocked treebanks (license restrictions)
- Comprehensive test suite (60 tests)
- Documentation:
  - README.md with usage examples
  - INSTALLATION.md with setup instructions
  - CONTRIBUTING.md with development guidelines

### Features
- Preserves all UD CoNLL-U fields including:
  - Required fields: FORM, LEMMA, UPOS, HEAD, DEPREL
  - Optional fields: XPOS, FEATS, DEPS, MISC
  - Comment metadata with original ordering
  - Multi-Word Tokens (contractions, etc.)
  - Empty nodes (enhanced dependencies)
- Raw field extraction to bypass conllu parser bugs
- Text-based validation with unified diff output
- Distinction between metadata and token line errors
- Local and remote (HuggingFace Hub) validation modes
- Test mode for quick validation (3 treebanks)
- Verbose output with progress tracking

### Technical Details
- Python 3.12+ support
- Dependencies:
  - conllu >= 5.0.0
  - datasets >= 4.0.0
  - pyarrow >= 14.0.0
  - pyyaml >= 6.0.2
  - python-dotenv >= 1.0.0
- Apache 2.0 License

---

## Version History Links

[Unreleased]: https://github.com/bot-zen/ud-hf-parquet-tools/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/bot-zen/ud-hf-parquet-tools/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/bot-zen/ud-hf-parquet-tools/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/bot-zen/ud-hf-parquet-tools/releases/tag/v1.0.0
