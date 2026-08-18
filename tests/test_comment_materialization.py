#!/usr/bin/env python3
"""Tests for DuckDB-backed comment marker materialization."""

import pytest


pytest.importorskip("duckdb")

from ud_hf_parquet_tools.comment_materialization import materialize_comment_markers_batch


def test_materialize_comment_markers_preserves_order():
    """Markers should be expanded in-place without changing comment order."""
    batch = {
        "sent_id": ["s1"],
        "text": ["Hello world."],
        "comments": [["newdoc id = doc-1", "__SENT_ID__", "__TEXT__", "newpar id = p1"]],
    }

    materialized = materialize_comment_markers_batch(batch)

    assert materialized["comments"][0] == [
        "newdoc id = doc-1",
        "sent_id = s1",
        "text = Hello world.",
        "newpar id = p1",
    ]


def test_materialize_comment_markers_without_required_columns_keeps_markers():
    """Missing sent_id/text columns should keep markers unchanged."""
    batch = {
        "comments": [["__SENT_ID__", "__TEXT__"]],
    }

    materialized = materialize_comment_markers_batch(batch)
    assert materialized["comments"][0] == ["__SENT_ID__", "__TEXT__"]


def test_materialize_comment_markers_without_comments_passthrough():
    """Batches without comments should be returned unchanged."""
    batch = {
        "sent_id": ["s1", "s2"],
        "text": ["A", "B"],
    }

    materialized = materialize_comment_markers_batch(batch)
    assert materialized == batch
