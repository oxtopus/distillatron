from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

_URL_PATTERN = re.compile(r"^-\s+\[([ x])\]\s+(https?://\S+)")
_BARE_URL_PATTERN = re.compile(r"^-\s+(https?://\S+)")


def parse_manifest(path: Path) -> list[dict]:
    """Parse manifest.md and return a list of URL entries.

    Each entry is a dict with keys: url, status, line_number.
    Status is one of: 'done', 'queued', 'new'.
    """
    if not path.exists():
        return []

    entries: list[dict] = []
    with open(path) as f:
        for i, line in enumerate(f, start=1):
            m = _URL_PATTERN.match(line)
            if m:
                status = "done" if m.group(1) == "x" else "queued"
                entries.append({"url": m.group(2), "status": status, "line_number": i})
                continue
            m = _BARE_URL_PATTERN.match(line)
            if m:
                entries.append({"url": m.group(1), "status": "new", "line_number": i})
    return entries


def update_manifest(path: Path, url: str, title: str | None = None) -> None:
    """Mark a URL as [x] Indexed with a timestamp sub-item in the manifest.

    Appends a sub-bullet under the URL line with the scrape timestamp.
    Existing [x] entries are left unchanged.
    """
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")

    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    label = title or url

    lines = path.read_text().splitlines(keepends=True)
    found = False
    for i, line in enumerate(lines):
        stripped = line.rstrip("\n")
        if url in stripped:
            if "[x]" in stripped:
                return  # already done
            if "[ ]" in stripped or stripped.startswith(f"- {url}"):
                prefix = "- [x]" if "[ ]" in stripped else "- [x]"
                lines[i] = f"{prefix} {url}\n"
                lines.insert(i + 1, f"    - Indexed: {now} — {label}\n")
                found = True
                break

    if not found:
        raise ValueError(f"URL not found in manifest: {url}")

    path.write_text("".join(lines))
