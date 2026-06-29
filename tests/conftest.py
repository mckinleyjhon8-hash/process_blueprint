"""Shared pytest fixtures."""

from __future__ import annotations

import os
import sys

import pytest

# Make `src/` importable without an install step.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from tests.sample_log import build_sample_log, write_sample_csv  # noqa: E402


@pytest.fixture(scope="session")
def sample_df():
    return build_sample_log(n_cases=60, seed=42)


@pytest.fixture()
def sample_csv(tmp_path):
    path = os.path.join(tmp_path, "sample_p2p.csv")
    return write_sample_csv(path, n_cases=60, seed=42)
