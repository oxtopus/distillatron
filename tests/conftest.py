from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Path:
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def sample_manifest() -> str:
    return (
        "- [x] https://example.com/done\n"
        "- [ ] https://example.com/queued\n"
        "- https://example.com/new\n"
    )


@pytest.fixture
def manifest_file(temp_dir: Path, sample_manifest: str) -> Path:
    path = temp_dir / "manifest.md"
    path.write_text(sample_manifest)
    return path
