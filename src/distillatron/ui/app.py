from __future__ import annotations

from textual.app import App

from .screens.article import ArticleScreen
from .screens.browse import BrowseScreen


class DistillatronApp(App):
    CSS_PATH = "app.css"
    TITLE = "Distillatron"
    SUB_TITLE = "news article indexing & semantic search"

    SCREENS = {
        "browse": BrowseScreen,
        "article": ArticleScreen,
    }

    def on_mount(self) -> None:
        self.push_screen("browse")


if __name__ == "__main__":
    DistillatronApp().run()
