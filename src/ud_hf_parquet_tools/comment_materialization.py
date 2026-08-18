"""DuckDB-powered helpers for materializing comment markers in Parquet rows."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping

import pyarrow as pa

_DUCKDB_CONN = None


def _get_duckdb_connection():
    """Get a reusable in-memory DuckDB connection.

    DuckDB is imported lazily so environments that only need generation/
    reconstruction logic do not fail at import time.
    """
    global _DUCKDB_CONN

    if _DUCKDB_CONN is None:
        try:
            import duckdb
        except ImportError as exc:
            raise ImportError(
                "duckdb is required for comment marker materialization. "
                "Install ud-hf-parquet-tools with duckdb support."
            ) from exc
        _DUCKDB_CONN = duckdb.connect(database=":memory:")

    return _DUCKDB_CONN


def _to_python_column(values: Any) -> list[Any]:
    """Convert column containers to plain Python lists."""
    if values is None:
        return []
    if hasattr(values, "to_pylist"):
        return values.to_pylist()
    if isinstance(values, list):
        return values
    if isinstance(values, tuple):
        return list(values)

    # Fallback for iterables with no random access.
    if isinstance(values, Iterable):
        return list(values)

    raise TypeError(f"Unsupported column container type: {type(values)}")


def materialize_comment_markers_batch(batch: Mapping[str, Any]) -> Dict[str, list[Any]]:
    """Materialize `__SENT_ID__`/`__TEXT__` markers in a batch.

    Args:
        batch: Columnar batch mapping (column -> list-like values), e.g.
            objects returned by ``datasets.Dataset.iter(batch_size=...)``.

    Returns:
        A new dictionary with the same columns where ``comments`` has marker
        placeholders replaced by full CoNLL-U metadata lines when possible.
    """
    if not batch:
        return {}

    python_batch: Dict[str, list[Any]] = {
        column_name: _to_python_column(column_values) for column_name, column_values in batch.items()
    }

    if "comments" not in python_batch:
        return python_batch

    has_sent_id = "sent_id" in python_batch
    has_text = "text" in python_batch

    sent_id_replacement = (
        "CASE WHEN sent_id IS NULL OR sent_id = '' THEN c ELSE 'sent_id = ' || sent_id END" if has_sent_id else "c"
    )
    text_replacement = "CASE WHEN text IS NULL OR text = '' THEN c ELSE 'text = ' || text END" if has_text else "c"

    query = f"""
        SELECT * REPLACE (
            CASE
                WHEN comments IS NULL THEN comments
                ELSE list_transform(
                    comments,
                    c -> CASE
                        WHEN c = '__SENT_ID__' THEN {sent_id_replacement}
                        WHEN c = '__TEXT__' THEN {text_replacement}
                        ELSE c
                    END
                )
            END AS comments
        )
        FROM batch_data
    """

    conn = _get_duckdb_connection()
    conn.register("batch_data", pa.Table.from_pydict(python_batch))
    try:
        arrow_result = conn.sql(query).arrow()
        if hasattr(arrow_result, "to_pydict"):
            materialized = arrow_result.to_pydict()
        else:
            materialized = arrow_result.read_all().to_pydict()
    finally:
        conn.unregister("batch_data")

    return materialized
