from __future__ import annotations

from distillatron.manifest import parse_manifest


class TestParseManifest:
    def test_parses_all_statuses(self, manifest_file):
        entries = parse_manifest(manifest_file)

        assert len(entries) == 3
        assert entries[0] == {"url": "https://example.com/done", "status": "done", "line_number": 1}
        assert entries[1] == {
            "url": "https://example.com/queued",
            "status": "queued",
            "line_number": 2,
        }
        assert entries[2] == {"url": "https://example.com/new", "status": "new", "line_number": 3}

    def test_empty_file_returns_empty_list(self, temp_dir):
        path = temp_dir / "nonexistent.md"
        entries = parse_manifest(path)
        assert entries == []

    def test_skips_non_url_lines(self, temp_dir):
        path = temp_dir / "manifest.md"
        path.write_text("- this is not a url\n- https://example.com/real\n")
        entries = parse_manifest(path)

        assert len(entries) == 1
        assert entries[0]["url"] == "https://example.com/real"
