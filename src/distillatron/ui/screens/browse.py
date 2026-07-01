from __future__ import annotations

import os

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
)

from ...db import get_db
from ...search import search as semantic_search

_WEB_MODE = os.environ.get("WEB_MODE", "") == "1"

_TUI_BINDINGS = [
    ("/", "toggle_search", "Search"),
    ("t", "clear_filter", "All topics"),
    ("b", "trigger_build", "Build"),
    ("enter", "view_article", "View"),
    ("q", "quit", "Quit"),
]

_WEB_BINDINGS = [
    ("/", "toggle_search", "Search"),
    ("t", "clear_filter", "All topics"),
    ("enter", "view_article", "View"),
    ("q", "quit", "Quit"),
]


class BrowseScreen(Screen):
    BINDINGS = _WEB_BINDINGS if _WEB_MODE else _TUI_BINDINGS

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Vertical(
                Label("Topics", classes="sidebar-header"),
                ListView(
                    ListItem(Label("All")),
                    id="topic-list",
                ),
                id="topics-sidebar",
            ),
            Vertical(
                Input(placeholder="Search articles...", id="search-input"),
                DataTable(id="article-table", cursor_type="row"),
                id="articles-panel",
            ),
            id="browse-layout",
        )
        yield Footer()

    def on_mount(self) -> None:
        self._articles: list[dict] = []
        self._active_topic: str | None = None
        self._search_timer: Timer | None = None

        search_input = self.query_one("#search-input", Input)
        search_input.display = False

        self._setup_table()
        self._load_topics()
        self._load_articles()

    def _setup_table(self) -> None:
        table = self.query_one("#article-table", DataTable)
        table.add_columns("Title", "Topics", "Source")
        table.show_header = True

    def _load_topics(self) -> None:
        try:
            db = get_db()
            tbl = db.open_table("articles")
            rows = tbl.search().limit(10000).to_list()
        except Exception:
            return

        counts: dict[str, int] = {}
        for r in rows:
            for topic in r.get("topics", []):
                counts[topic] = counts.get(topic, 0) + 1

        lst = self.query_one("#topic-list", ListView)
        lst.clear()

        all_item = ListItem(Label(f"All ({len(rows)})"))
        lst.append(all_item)

        for topic, count in sorted(counts.items(), key=lambda x: -x[1]):
            lst.append(ListItem(Label(f"{topic} ({count})")))

    def _load_articles(self, topic: str | None = None) -> None:
        try:
            db = get_db()
            tbl = db.open_table("articles")
            rows = tbl.search().limit(10000).to_list()
        except Exception:
            return

        if topic:
            topic_lower = topic.lower()
            rows = [r for r in rows if topic_lower in [t.lower() for t in r.get("topics", [])]]

        self._articles = rows
        table = self.query_one("#article-table", DataTable)
        table.clear()
        for r in rows:
            title = r.get("title", r.get("url", ""))
            tags = ", ".join(r.get("topics", []))
            source = r.get("source", "")
            table.add_row(title, tags, source, key=r.get("id"))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id != "topic-list":
            return
        if event.index == 0:
            self._active_topic = None
            self._load_articles()
        elif event.item is not None:
            label = str(event.item.children[0].content)
            topic = label.rsplit(" (", 1)[0]
            self._active_topic = topic
            self._load_articles(topic)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "search-input":
            return
        query = event.value.strip()
        if not query:
            self._load_articles(self._active_topic)
            return
        if hasattr(self, "_search_timer") and self._search_timer is not None:
            self._search_timer.stop()
        self._search_timer = self.set_timer(0.3, self._do_search)

    def _do_search(self) -> None:
        inp = self.query_one("#search-input", Input)
        query = inp.value.strip()
        if not query:
            return
        self._run_search(query)

    @work(exclusive=True)
    async def _run_search(self, query: str) -> None:
        try:
            db = get_db()
            results = semantic_search(query, db, topic=self._active_topic, limit=50)
        except Exception:
            return

        self._articles = list(results) if results else []
        table = self.query_one("#article-table", DataTable)
        table.clear()
        for r in self._articles:
            title = r.get("title", r.get("url", ""))
            tags = ", ".join(r.get("topics", []))
            source = r.get("source", "")
            table.add_row(title, tags, source, key=r.get("id"))

    def action_toggle_search(self) -> None:
        inp = self.query_one("#search-input", Input)
        if inp.display:
            inp.display = False
            inp.value = ""
            self._load_articles(self._active_topic)
        else:
            inp.display = True
            inp.focus()

    def action_clear_filter(self) -> None:
        self._active_topic = None
        self._load_articles()
        lst = self.query_one("#topic-list", ListView)
        lst.index = 0

    def action_view_article(self) -> None:
        table = self.query_one("#article-table", DataTable)
        if table.row_count == 0:
            return
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        if row_key is None:
            return
        article_id = row_key.row_key.value if row_key.row_key else None
        if article_id is None:
            return
        for a in self._articles:
            if a.get("id") == article_id:
                self.app.push_screen("article", a)
                return

    def action_trigger_build(self) -> None:
        self._run_build()

    @work(exclusive=True)
    async def _run_build(self) -> None:
        from ...ingest import process_manifest

        process_manifest()
        self._load_topics()
        self._load_articles(self._active_topic)
