# Release Process

This document describes how to publish a new release of `ud-hf-parquet-tools`.

**Note**: This project uses [uv](https://github.com/astral-sh/uv) for package management. All commands use `uv pip` instead of plain `pip` for consistency with the project's development workflow.

## Table of Contents

1. [Pre-Release Checklist](#pre-release-checklist)
2. [Version Numbering](#version-numbering)
3. [Release Steps](#release-steps)
4. [Post-Release Steps](#post-release-steps)
5. [Troubleshooting](#troubleshooting)

## Pre-Release Checklist

Before creating a new release, ensure the following are complete:

### 1. Code Quality

- [ ] All tests pass: `pytest`
- [ ] Code is formatted: `ruff format src/ tests/`
- [ ] Linting passes: `ruff check src/ tests/`
- [ ] No outstanding bugs or critical issues
- [ ] All new features have tests
- [ ] Documentation is up to date

### 2. Documentation

- [ ] `README.md` reflects current functionality
- [ ] `INSTALLATION.md` has correct installation instructions
- [ ] `CONTRIBUTING.md` is current (if exists)
- [ ] Docstrings are complete and accurate
- [ ] Usage examples work correctly

### 3. Dependencies

- [ ] All dependencies in `pyproject.toml` are up to date
- [ ] No security vulnerabilities in dependencies
- [ ] Test with minimum and maximum supported Python versions

### 4. Changelog

- [ ] Create or update `CHANGELOG.md` with all changes since last release
- [ ] Group changes by category (Added, Changed, Fixed, Removed, etc.)
- [ ] Include migration notes for breaking changes

## Version Numbering

We use [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes that require user action
- **MINOR**: New features, backward-compatible
- **PATCH**: Bug fixes, backward-compatible

### Examples

- `1.0.0` → `1.0.1`: Bug fix
- `1.0.0` → `1.1.0`: New feature added
- `1.0.0` → `2.0.0`: Breaking API change

## Release Steps

### Step 1: Update Version Number

Edit `pyproject.toml` and update the version:

```toml
[project]
name = "ud-hf-parquet-tools"
version = "X.Y.Z"  # Update this line
```

### Step 2: Update CHANGELOG.md

Create or update `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing functionality

### Fixed
- Bug fixes

### Removed
- Removed features
```

### Step 3: Commit Version Changes

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to X.Y.Z"
```

### Step 4: Create Git Tag

Create an annotated tag for the release:

```bash
git tag -a vX.Y.Z -m "Release version X.Y.Z"
```

**Tag naming convention**: Use `vX.Y.Z` format (e.g., `v1.0.1`, `v1.1.0`, `v2.0.0`)

### Step 5: Push Changes and Tag

```bash
# Push the commit
git push origin main

# Push the tag
git push origin vX.Y.Z
```

### Step 6: Build Distribution Packages

Clean any previous builds and create new distribution packages:

```bash
# Remove old builds
rm -rf dist/ build/ *.egg-info

# Build the package
uv build
```

This creates two files in the `dist/` directory:
- `ud_hf_parquet_tools-X.Y.Z-py3-none-any.whl` (wheel)
- `ud_hf_parquet_tools-X.Y.Z.tar.gz` (source)

### Step 7: Test on TestPyPI (Optional but Recommended)

Upload to TestPyPI first to verify everything works:

```bash
# Upload to TestPyPI
uv publish --publish-url https://test.pypi.org/legacy/

# Test installation from TestPyPI
uv pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    ud-hf-parquet-tools==X.Y.Z

# Verify it works
ud-hfp-tools --help
```

**Note**: TestPyPI requires a separate account and API token. Get your token from https://test.pypi.org/manage/account/token/

### Step 8: Publish to PyPI

Once verified, upload to the production PyPI:

```bash
# Upload to PyPI
uv publish
```

**Authentication**: `uv publish` will prompt for credentials or use stored tokens.

**Getting a PyPI API token**:
1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Name: `ud-hf-parquet-tools-releases`
4. Scope: "Project: ud-hf-parquet-tools" (after first upload) or "Entire account"
5. Copy the token (starts with `pypi-`)
6. Store securely (you won't see it again)

**Save token for reuse** (Option 1 - Environment variable):
```bash
export UV_PUBLISH_TOKEN=pypi-YOUR_TOKEN_HERE
```

**Save token for reuse** (Option 2 - keyring):
```bash
# uv uses the system keyring for secure storage
# On first publish, it will save credentials automatically
```

**Save token for reuse** (Option 3 - .pypirc):
Create `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE

[testpypi]
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

Then set permissions:
```bash
chmod 600 ~/.pypirc
```

### Step 9: Create GitHub Release

1. Go to https://github.com/bot-zen/ud-hf-parquet-tools/releases
2. Click "Draft a new release"
3. Choose the tag you created (`vX.Y.Z`)
4. Release title: `Version X.Y.Z` or descriptive title
5. Description: Copy from CHANGELOG.md for this version
6. Attach the distribution files from `dist/` (optional)
7. Click "Publish release"

### Step 10: Verify Installation

Test that users can install the new version:

```bash
# Create a fresh virtual environment
uv venv test_env
source test_env/bin/activate

# Install from PyPI
uv pip install ud-hf-parquet-tools==X.Y.Z

# Verify version
uv pip show ud-hf-parquet-tools

# Test functionality
ud-hfp-tools --help

# Cleanup
deactivate
rm -rf test_env
```

## Post-Release Steps

### 1. Announce the Release

- [ ] Update project README.md badges if needed
- [ ] Post announcement on relevant channels
- [ ] Update documentation site (if applicable)
- [ ] Notify dependent projects (like `universal_dependencies` dataset)

### 2. Update Dependent Projects

If this library is used by other projects (e.g., the Universal Dependencies dataset loader), update their dependencies:

**For the universal_dependencies dataset**:

1. Update dependency version in scripts:
   ```python
   # tools/04_generate_parquet.py
   # tools/05_validate_parquet.py
   # Update the dependency in the script header if pinning to specific version
   ```

2. Update documentation if new features are available

3. Test integration with the new version

### 3. Monitor for Issues

- [ ] Watch GitHub issues for bug reports
- [ ] Monitor PyPI download statistics
- [ ] Check for installation problems

## Troubleshooting

### Build Fails

**Problem**: `uv build` fails

**Solutions**:
```bash
# Clear cache
rm -rf dist/ build/ *.egg-info __pycache__ .pytest_cache

# Ensure uv is up to date
uv self update

# Try again
uv build
```

### Upload Fails: "File already exists"

**Problem**: Version already exists on PyPI

**Solution**: You cannot replace an existing version. You must:
1. Delete the dist files
2. Increment the version number (even to X.Y.Z.post1 for hotfixes)
3. Rebuild and reupload

### Upload Fails: Authentication Error

**Problem**: Invalid credentials

**Solutions**:
- Ensure username is exactly `__token__` (two underscores)
- Verify token starts with `pypi-` and is complete
- Check token hasn't expired or been revoked
- Ensure token has correct scope (project or account)

### Tag Already Exists

**Problem**: Git tag already exists

**Solutions**:
```bash
# Delete local tag
git tag -d vX.Y.Z

# Delete remote tag
git push origin :refs/tags/vX.Y.Z

# Recreate tag
git tag -a vX.Y.Z -m "Release version X.Y.Z"
git push origin vX.Y.Z
```

### Version Mismatch

**Problem**: PyPI shows wrong version after upload

**Likely cause**: Cached build artifacts

**Solution**:
```bash
# Clean everything
rm -rf dist/ build/ *.egg-info __pycache__
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Verify version in pyproject.toml
grep "version = " pyproject.toml

# Rebuild
uv build

# Verify built version
unzip -p dist/ud_hf_parquet_tools-*.whl ud_hf_parquet_tools/__init__.py | grep version
```

## Quick Reference: Complete Release

```bash
# 1. Update version
vim pyproject.toml  # Change version = "X.Y.Z"

# 2. Update changelog
vim CHANGELOG.md    # Add release notes

# 3. Run tests
pytest
ruff format src/ tests/
ruff check src/ tests/

# 4. Commit and tag
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to X.Y.Z"
git tag -a vX.Y.Z -m "Release version X.Y.Z"
git push origin main
git push origin vX.Y.Z

# 5. Build
rm -rf dist/ build/ *.egg-info
uv build

# 6. Test upload (optional)
uv publish --publish-url https://test.pypi.org/legacy/

# 7. Production upload
uv publish

# 8. Verify
uv pip install --upgrade ud-hf-parquet-tools==X.Y.Z
ud-hfp-tools --help

# 9. Create GitHub release
# Go to https://github.com/bot-zen/ud-hf-parquet-tools/releases
```

## Emergency Hotfix Release

For critical bugs that need immediate release:

1. Create a hotfix branch from the tag:
   ```bash
   git checkout -b hotfix/X.Y.Z+1 vX.Y.Z
   ```

2. Make the minimal fix

3. Update version to X.Y.Z+1 (increment patch)

4. Follow normal release process

5. Merge back to main:
   ```bash
   git checkout main
   git merge hotfix/X.Y.Z+1
   git push origin main
   ```

## Version History

Track your releases:

- `v1.0.0` - Initial release (YYYY-MM-DD)
- `v1.0.1` - Bug fix release
- `v1.1.0` - Added new validation features
- etc.

---

**Questions or issues?** Open an issue at https://github.com/bot-zen/ud-hf-parquet-tools/issues
