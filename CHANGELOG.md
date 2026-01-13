# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial CHANGELOG.md
- RELEASE.md with comprehensive release process documentation

### Changed
- Applied ruff formatting and linting across codebase

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

[Unreleased]: https://github.com/bot-zen/ud-hf-parquet-tools/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/bot-zen/ud-hf-parquet-tools/releases/tag/v1.0.0
