# Distillatron

A vibe-coding experiment to index news articles with semantic search. Paste URLs into a manifest file, run a single command, and get a searchable, classified database of articles with a REST API and UI.

## Quick start

```bash
# 1. Install dependencies
make install

# 2. Configure API keys
cp .env.example .env
# Edit .env with your Firecrawl and DeepSeek keys

# 3. Add URLs to your manifest
echo "- https://example.com/article" > manifest.md

# 4. Scrape, embed, classify, and index
make build

# 5. Start the API
make up
```

Then open `http://localhost:8000` for the web UI, or `http://localhost:8000/docs` for the Swagger API docs.

## How it works

```
manifest.md  ──►  Firecrawl scrape  ──►  embed (local or OpenAI)  ──►  DeepSeek classify  ──►  LanceDB
     │                                                                                           │
     └── updates [x] + timestamp ◄──────────────────────────────────────────────────────────────┘
                                                                                                 │
                                                                                    FastAPI  ◄──┘
```

1. **Parse** `manifest.md` for URLs with status (`[ ]` queued, `[x]` done, bare new)
2. **Scrape** each URL via Firecrawl → clean markdown + title
3. **Embed** content into a vector (384d or 1536d depending on backend)
4. **Classify** into topic tags via DeepSeek (two-pass: raw tags → normalize)
5. **Store** everything in LanceDB (embedded, local-first)
6. **Update** the manifest in-place with `[x]` and a timestamp

The build is idempotent — already-indexed URLs are skipped.

## Configuration

All settings live in `.env`:

| Variable                 | Required                 | Default                    | Description                         |
| ------------------------ | ------------------------ | -------------------------- | ----------------------------------- |
| `FIRECRAWL_API_KEY`      | yes                      | —                          | Firecrawl API key for scraping      |
| `DEEPSEEK_API_KEY`       | yes                      | —                          | DeepSeek API key for classification |
| `DEEPSEEK_BASE_URL`      | no                       | `https://api.deepseek.com` | DeepSeek endpoint                   |
| `DEEPSEEK_MODEL`         | no                       | `deepseek-v4-flash`        | Model for topic classification      |
| `EMBEDDING_BACKEND`      | no                       | `openai`                   | `local` (free, offline) or `openai` |
| `LOCAL_EMBEDDING_MODEL`  | no                       | `BAAI/bge-small-en-v1.5`   | Model for local embeddings          |
| `OPENAI_API_KEY`         | only if `backend=openai` | —                          | OpenAI API key for embeddings       |
| `OPENAI_EMBEDDING_MODEL` | no                       | `text-embedding-3-small`   | OpenAI embedding model              |
| `LANCEDB_URI`            | no                       | `data/lancedb`             | LanceDB storage directory           |

### Embedding backends

**Local** (default in `.env.example`): Uses `fastembed` with ONNX runtime. No API key, no network calls during embedding. First run downloads the model (~130 MB). Models:

- `BAAI/bge-small-en-v1.5` (384d, fast)
- `BAAI/bge-base-en-v1.5` (768d, better quality)

**OpenAI**: Uses `text-embedding-3-small` (1536d). Requires an OpenAI API key with credits. Set `EMBEDDING_BACKEND=openai` and provide `OPENAI_API_KEY`.

Switching backends requires clearing the database: `rm -rf data/lancedb`.

## Manifest format

Create `manifest.md` in the project root. One URL per line:

```markdown
- https://example.com/article-one
- [ ] https://example.com/queued
- [x] https://example.com/already-done
```

| Syntax              | Meaning                    |
| ------------------- | -------------------------- |
| `- https://...`     | New URL, will be processed |
| `- [ ] https://...` | Queued (same as bare)      |
| `- [x] https://...` | Done, skipped on build     |

After processing, each URL is updated in-place:

```markdown
- [x] https://example.com/article-one
  - Indexed: 2026-06-29 17:55:41 UTC — Article Title Here
```

The manifest is gitignored. See `MANIFEST.md.example` for reference.

## Commands

| Command             | Description                                     |
| ------------------- | ----------------------------------------------- |
| `make install`      | Install dependencies (`uv sync`)                |
| `make build`        | Run the ingest pipeline (process manifest)      |
| `make up`           | Start server at `http://localhost:8000` (web UI + API) |
| `make tui`          | Launch terminal UI (Textual)                          |
| `make test`         | Run tests (`pytest`)                            |
| `make lint`         | Run linter (`ruff check`)                       |
| `make fmt`          | Format code (`ruff format`)                     |
| `make clean`        | Remove data, caches, and venv                   |
| `make kernel`       | Register Jupyter kernel for notebooks           |
| `make notebook`     | Launch Jupyter in `notebooks/`                  |
| `make docker-build` | Build Docker image                              |
| `make docker-up`    | Run via Docker Compose                          |

## API

Start with `make up`, then visit `http://localhost:8000/docs` for interactive docs.

| Method | Path                                    | Description             |
| ------ | --------------------------------------- | ----------------------- |
| `GET`  | `/health`                               | Health check            |
| `GET`  | `/search?q=...&topic=...&limit=10`      | Semantic search         |
| `GET`  | `/articles?topic=...&limit=20&offset=0` | List articles           |
| `GET`  | `/articles/{id}`                        | Full article content    |
| `GET`  | `/topics`                               | All topics with counts  |
| `POST` | `/build`                                | Trigger ingest pipeline |

### Example

```bash
# Semantic search
curl "http://localhost:8000/search?q=llm+state+mutation&limit=3"

# Filter by topic
curl "http://localhost:8000/search?q=architecture&topic=AI+architecture"

# List all topics
curl "http://localhost:8000/topics"

# Get articles filtered by topic
curl "http://localhost:8000/articles?topic=state+mutation"
```

## Interfaces

Distillatron has two UIs sharing the same layout: topics sidebar, searchable article table, and article detail view.

### Web UI

Start with `make up`, open `http://localhost:8000`.

- Topics sidebar with article counts — click a topic to filter
- Search bar with debounced semantic search — type to find articles
- Article titles link directly to the original URL; a "details" link opens the Distillatron article page
- Topic tags in each row are clickable filters
- Read-only — no build action exposed
- Built with HTMX + Jinja2, served by FastAPI

### Terminal UI

Start with `make tui` (requires a terminal, not a browser).

- Same layout as the web UI, keyboard-navigated
- `/` toggles the search bar, type to search
- `↑`/`↓` to scroll articles, `Enter` to view full content
- Click a topic in the sidebar to filter
- `t` resets the topic filter
- `b` triggers a build to index new URLs from the manifest
- `q` to quit
- Built with Textual, uses direct module imports (no network calls for search)

## Project layout

```
distillatron/
├── manifest.md              # Your URL list (gitignored)
├── MANIFEST.md.example      # Reference manifest
├── pyproject.toml           # Dependencies and tool config
├── Makefile                 # Task shortcuts
├── .env                     # API keys (gitignored)
├── .env.example             # Key template
├── src/distillatron/           # Application code
│   ├── __init__.py
│   ├── config.py                # Settings from env
│   ├── db.py                    # LanceDB schema and connection
│   ├── manifest.py              # Manifest parser and updater
│   ├── scrape.py                # Firecrawl integration
│   ├── embed.py                 # Embedding (local or OpenAI)
│   ├── classify.py              # DeepSeek topic classification
│   ├── ingest.py                # Pipeline orchestrator
│   ├── search.py                # Semantic search
│   ├── routes.py                # FastAPI REST endpoints
│   ├── main.py                  # App entry point
│   ├── ui/                      # Terminal UI (Textual)
│   │   ├── app.py               # Textual App, screens, key bindings
│   │   ├── app.css              # Dark theme styling
│   │   └── screens/
│   │       ├── browse.py        # Topics sidebar + article table + search
│   │       └── article.py       # Full article content
│   └── web/                     # Web UI (HTMX + Jinja2)
│       ├── routes.py            # HTML page/fragment routes
│       ├── static/style.css     # Web styling
│       └── templates/           # Jinja2 templates
├── tests/                   # Test suite
├── notebooks/               # Jupyter experimentation
├── docker/                  # Dockerfile and Compose config
├── terraform/               # Infrastructure skeleton
└── data/                    # LanceDB storage (gitignored)
```

## Tech stack

Python 3.12+ / FastAPI / LanceDB / Firecrawl / DeepSeek / fastembed / uv / ruff / Docker
