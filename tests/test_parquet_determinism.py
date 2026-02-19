"""Determinism tests for generated parquet files."""

from hashlib import sha256
from pathlib import Path

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
