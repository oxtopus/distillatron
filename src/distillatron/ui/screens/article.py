from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Markdown


class ArticleScreen(Screen):
    BINDINGS = [
        ("escape", "pop_screen", "Back"),
        ("o", "open_url", "Open in browser"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("", id="article-title")
        yield Label("", id="article-meta")
        yield Label("", id="article-topics")
        yield Markdown("", id="article-content")
        yield Footer()

    def on_mount(self, article: dict | None = None) -> None:
        if article is None:
            return
        self._article = article
        title = self.query_one("#article-title", Label)
        title.update(article.get("title", article.get("url", "")))

        meta = self.query_one("#article-meta", Label)
        source = article.get("source", "")
        scraped = article.get("scraped_at", "")
        meta.update(f"{source}  ·  {scraped}" if scraped else source)

        topics = self.query_one("#article-topics", Label)
        topic_list = article.get("topics", [])
        topics.update("  ".join(f"#{t}" for t in topic_list))

        content = self.query_one("#article-content", Markdown)
        text = article.get("content", "*No content available.*")
        content.update(text)

    def action_open_url(self) -> None:
        import webbrowser

        webbrowser.open(self._article["url"])
