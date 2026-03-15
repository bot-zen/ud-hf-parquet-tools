"""Determinism tests for generated parquet files."""

from hashlib import sha256
from pathlib import Path

import pyarrow.parquet as pq

from ud_hf_parquet_tools.generator import generate_parquet_for_treebank


def _write_conllu(path: Path, sent_id: str, token: str) -> None:
    path.write_text(
        f"# sent_id = {sent_id}\n"
        f"# text = {token}\n"
        f"1\t{token}\t{token.lower()}\tNOUN\t_\t_\t0\troot\t_\t_\n\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_generate_parquet_is_bit_reproducible_with_reordered_files(tmp_path: Path) -> None:
    ud_repos_dir = tmp_path / "UD_repos"
    treebank_dir = ud_repos_dir / "UD_Test-Treebank"
    treebank_dir.mkdir(parents=True)

    _write_conllu(treebank_dir / "a.conllu", sent_id="a-1", token="Alpha")
    _write_conllu(treebank_dir / "b.conllu", sent_id="b-1", token="Beta")

    metadata_a = {
        "dirname": "UD_Test-Treebank",
        "splits": {"train": {"files": ["b.conllu", "a.conllu"]}},
    }
    metadata_b = {
        "dirname": "UD_Test-Treebank",
        "splits": {"train": {"files": ["a.conllu", "b.conllu"]}},
    }

    out_a = tmp_path / "out_a"
    out_b = tmp_path / "out_b"

    assert generate_parquet_for_treebank(
        "xx_test", metadata_a, ud_repos_dir, out_a, verbose=False, overwrite=True
    )
    parquet_a = out_a / "xx_test" / "train.parquet"
    hash_a = _sha256(parquet_a)

    assert generate_parquet_for_treebank(
        "xx_test", metadata_b, ud_repos_dir, out_b, verbose=False, overwrite=True
    )
    parquet_b = out_b / "xx_test" / "train.parquet"
    hash_b = _sha256(parquet_b)

    assert hash_a == hash_b

    # Re-running overwrite with unchanged inputs should remain byte-identical.
    assert generate_parquet_for_treebank(
        "xx_test", metadata_a, ud_repos_dir, out_a, verbose=False, overwrite=True
    )
    assert _sha256(parquet_a) == hash_a


def test_overwrite_preserves_existing_bytes_when_table_is_equal(tmp_path: Path) -> None:
    """Do not replace an existing parquet file when only byte encoding differs."""
    ud_repos_dir = tmp_path / "UD_repos"
    treebank_dir = ud_repos_dir / "UD_Test-Treebank"
    treebank_dir.mkdir(parents=True)

    _write_conllu(treebank_dir / "a.conllu", sent_id="a-1", token="Alpha")
    _write_conllu(treebank_dir / "b.conllu", sent_id="b-1", token="Beta")

    metadata = {
        "dirname": "UD_Test-Treebank",
        "splits": {"train": {"files": ["a.conllu", "b.conllu"]}},
    }
    out = tmp_path / "out"

    assert generate_parquet_for_treebank(
        "xx_test", metadata, ud_repos_dir, out, verbose=False, overwrite=True
    )
    parquet_path = out / "xx_test" / "train.parquet"

    # Rewrite with different encoding parameters but identical logical table.
    table = pq.read_table(parquet_path)
    pq.write_table(table, parquet_path, compression="gzip")
    legacy_hash = _sha256(parquet_path)

    assert generate_parquet_for_treebank(
        "xx_test", metadata, ud_repos_dir, out, verbose=False, overwrite=True
    )
    assert _sha256(parquet_path) == legacy_hash


def test_without_overwrite_missing_split_does_not_rewrite_existing_splits(tmp_path: Path) -> None:
    """With partial outputs and overwrite disabled, regenerate only missing splits."""
    ud_repos_dir = tmp_path / "UD_repos"
    treebank_dir = ud_repos_dir / "UD_Test-Treebank"
    treebank_dir.mkdir(parents=True)

    _write_conllu(treebank_dir / "train.conllu", sent_id="tr-1", token="Train")
    _write_conllu(treebank_dir / "test.conllu", sent_id="te-1", token="Test")

    metadata = {
        "dirname": "UD_Test-Treebank",
        "splits": {
            "train": {"files": ["train.conllu"]},
            "test": {"files": ["test.conllu"]},
        },
    }
    out = tmp_path / "out"

    assert generate_parquet_for_treebank(
        "xx_test", metadata, ud_repos_dir, out, verbose=False, overwrite=True
    )
    train_path = out / "xx_test" / "train.parquet"
    test_path = out / "xx_test" / "test.parquet"
    train_hash_before = _sha256(train_path)

    # Simulate interrupted run: test split missing, train split already present.
    test_path.unlink()

    assert generate_parquet_for_treebank(
        "xx_test", metadata, ud_repos_dir, out, verbose=False, overwrite=False
    )
    assert _sha256(train_path) == train_hash_before
    assert test_path.exists()
