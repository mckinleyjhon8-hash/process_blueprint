"""Tests for the ingest layer."""

from __future__ import annotations

import os

import pandas as pd
import pytest

from process_blueprint.ingest import ingest, IngestError, CASE, ACT, TS


def test_ingest_csv_canonical(sample_csv):
    df, notes = ingest(sample_csv)
    assert {CASE, ACT, TS}.issubset(df.columns)
    assert len(df) > 0
    assert df[TS].notna().all()
    # Per-case events must be in chronological order (the property that matters;
    # pm4py.format_dataframe groups by case, so global order is not guaranteed).
    for _, case_df in df.groupby(CASE):
        assert case_df[TS].is_monotonic_increasing
    assert any("Ingested" in n for n in notes)


def test_ingest_with_custom_mapping(tmp_path):
    raw = pd.DataFrame(
        {
            "ticket": ["A", "A", "B"],
            "step": ["Open", "Close", "Open"],
            "when": ["2026-01-01", "2026-01-02", "2026-01-03"],
        }
    )
    p = os.path.join(tmp_path, "raw.csv")
    raw.to_csv(p, index=False)
    df, _ = ingest(
        p, column_mapping={"case_id": "ticket", "activity": "step", "timestamp": "when"}
    )
    assert {CASE, ACT, TS}.issubset(df.columns)
    assert df[CASE].nunique() == 2


def test_ingest_missing_columns_raises(tmp_path):
    bad = pd.DataFrame({"foo": [1], "bar": [2]})
    p = os.path.join(tmp_path, "bad.csv")
    bad.to_csv(p, index=False)
    with pytest.raises(IngestError):
        ingest(p)


def test_ingest_unknown_file_raises():
    with pytest.raises(IngestError):
        ingest("does_not_exist.csv")
