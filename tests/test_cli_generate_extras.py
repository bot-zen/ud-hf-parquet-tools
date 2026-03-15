"""Tests for generate CLI extra parquet detection/pruning helpers."""

from pathlib import Path

from ud_hf_parquet_tools.cli import (
    _prune_extra_parquet_entries,
    _scan_extra_parquet_entries,
)


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x")


def test_scan_full_scope_finds_extra_treebank_and_split(tmp_path: Path) -> None:
    output_dir = tmp_path / "parquet"
    _touch(output_dir / "en_ewt" / "train.parquet")
    _touch(output_dir / "en_ewt" / "old.parquet")
    _touch(output_dir / "old_treebank" / "test.parquet")

    expected = {"en_ewt": {"train.parquet"}}
    extras = _scan_extra_parquet_entries(output_dir, expected, full_scope=True)

    assert (output_dir / "old_treebank") in extras.extra_treebank_dirs
    assert (output_dir / "en_ewt" / "old.parquet") in extras.extra_split_files
    assert extras.has_entries()


def test_scan_subset_scope_ignores_unselected_treebank_dirs(tmp_path: Path) -> None:
    output_dir = tmp_path / "parquet"
    _touch(output_dir / "en_ewt" / "train.parquet")
    _touch(output_dir / "en_ewt" / "old.parquet")
    _touch(output_dir / "other_treebank" / "test.parquet")

    expected = {"en_ewt": {"train.parquet"}}
    extras = _scan_extra_parquet_entries(output_dir, expected, full_scope=False)

    assert not extras.extra_treebank_dirs
    assert (output_dir / "en_ewt" / "old.parquet") in extras.extra_split_files
    assert extras.has_entries()


def test_prune_removes_extras_but_keeps_expected_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "parquet"
    expected_file = output_dir / "en_ewt" / "train.parquet"
    _touch(expected_file)
    _touch(output_dir / "en_ewt" / "old.parquet")
    _touch(output_dir / "en_ewt" / "README.txt")
    _touch(output_dir / "old_treebank" / "test.parquet")

    expected = {"en_ewt": {"train.parquet"}}
    extras_before = _scan_extra_parquet_entries(output_dir, expected, full_scope=True)
    assert extras_before.has_entries()

    _prune_extra_parquet_entries(extras_before)

    extras_after = _scan_extra_parquet_entries(output_dir, expected, full_scope=True)
    assert not extras_after.has_entries()
    assert expected_file.exists()
