# SPEC — Distillatron

## Mission

Distillatron maintains a record of news articles, indexes their content for semantic search, and organizes
them by topic. The user curates a markdown manifest of URLs; the system scrapes, embeds, classifies, and
makes everything searchable.

## Architecture

```
manifest.md               ← user edits (bullet list of URLs + processing status)
     │
     ▼
make build / CLI          ← idempotent: skips already-indexed URLs
     │
     ├── Firecrawl ────────► scrape URL → markdown + title
     ├── Embedding ────────► fastembed (local, 384d) or OpenAI (1536d) → vector
     ├── DeepSeek ─────────► classify → raw topics → normalize → final topics
     ├── LanceDB ──────────► store: url, title, content, embedding, topics, source, scraped_at
     └── manifest.md ──────► update: [x] Indexed + timestamp under each processed URL
     │
     ▼
Textual TUI               ← terminal: make tui. Keyboard-first, direct imports.
     │                      Browse screen (topics sidebar + article table + search)
     │                      Article screen (full content)
     │
     ▼
FastAPI                   ← serve both web UI and REST API: make up
     │
     ├── Web UI (HTMX)    ← / → browse page, /web/... → fragments, Jinja2 templates
     │                      Read-only: no build action.
     ├── REST API         ← /search, /articles, /articles/{id}, /topics, /build
     │
     ▼
LanceDB                  ← embedded mode, data/ directory
```

## Tech Stack

| Layer              | Choice                        | Rationale                                                                   |
| ------------------ | ----------------------------- | --------------------------------------------------------------------------- |
| Language           | Python (~3.12+)               | FastAPI ecosystem, strong ML/vector library support                         |
| Framework          | FastAPI                       | Async, Pydantic-native, good container ergonomics                           |
| Package manager    | uv                            | Fast (Rust), pip-compatible, lockfile, virtual env management               |
| Formatter / Linter | ruff                          | Fast (Rust), replaces flake8/isort/black, single config                     |
| Vector DB          | LanceDB                       | Columnar, embedded or server mode, local-first, S3-compatible               |
| Embeddings         | fastembed (local) or OpenAI text-embedding-3-small | fastembed default: free, offline, ONNX runtime, 384d vectors. OpenAI optional for higher quality (1536d). EMBEDDING_BACKEND env var switches. |
| Classification     | DeepSeek (via OpenAI SDK)                           | OpenAI-compatible endpoint. deepseek-v4-flash. DEEPSEEK_API_KEY from env.                                                                       |
| Scraping           | Firecrawl SDK (V1)                                  | V1FirecrawlApp. Handles JS pages, returns clean markdown. FIRECRAWL_API_KEY from env.                                                           |
| UI (TUI)           | Textual                                             | Terminal-native, keyboard navigation, direct module imports. Build enabled.                                              |
| UI (Web)           | HTMX + Jinja2, served by FastAPI                    | Lightweight, no build step. REST API for data. Read-only (no build action). Same layout as TUI.                          |
| Notebooks          | Jupyter                                             | Iterative experimentation, shared kernel with project venv                                                                 |
| Container runtime  | Docker + Docker Compose                             | Local dev mirrors production topology                                                                                                           |
| Infrastructure     | Terraform                                           | Cloud-agnostic modules, provider chosen at deploy time                                                                                          |
| Frontend           | Deferred — replaced by Textual UI                   | Textual covers TUI + browser; no separate web frontend needed                                                                                   |
| Cloud              | Unspecified                                         | Terraform written agnostic; AWS or GCP likely candidates                                                                                        |

## Source modules

| Module               | Purpose                                                                      |
| -------------------- | ---------------------------------------------------------------------------- |
| `src/db.py`          | LanceDB connection, `articles` table schema (LanceModel), `get_db()`         |
| `src/manifest.py`    | Parse `manifest.md`: extract URLs with status. Update manifest in-place.     |
| `src/scrape.py`      | Firecrawl V1 SDK: URL → title + markdown content                             |
| `src/embed.py`       | fastembed (local, default) or OpenAI: text → vector                          |
| `src/classify.py`    | DeepSeek (deepseek-v4-flash): content → raw topic tags → normalize → topics  |
| `src/ingest.py`      | Pipeline orchestrator: manifest → scrape → embed → classify → store → update |
| `src/search.py`      | Embed query → ANN search LanceDB → ranked results                            |
| `src/routes.py`      | FastAPI router: /search, /articles, /articles/{id}, /topics, /build          |
| `src/main.py`        | FastAPI app entry point, lifespan, router registration                       |
| `src/ui/app.py`      | Textual App class, SCREENS, key bindings, CSS_PATH                           |
| `src/ui/app.css`     | Styling: dark theme, layout, widget classes                                  |
| `src/ui/screens/`    | Two screens: browse (topics + table + search), article detail                |
| `src/web/routes.py`  | Web routes: /, /web/topics, /web/articles, /web/search, /web/articles/{id}   |
| `src/web/templates/` | Jinja2 templates: base, browse, article, article_list, search_results, topic_list |
| `src/web/static/`    | CSS for web UI                                                                |

## LanceDB schema — `articles` table

| Column     | Type        | Description                          |
| ---------- | ----------- | ------------------------------------ |
| id         | str         | UUID, primary key                    |
| url        | str         | Article URL (unique, used for dedup) |
| title      | str         | Article title                        |
| content    | str         | Full markdown content                |
| embedding  | list[float] | Vector from embedding model (384d fastembed, or 1536d OpenAI) |
| topics     | list[str]   | Normalized topic tags                |
| source     | str         | Domain extracted from URL            |
| scraped_at | datetime    | ISO timestamp of scraping            |

## API endpoints

| Method | Path                                  | Description                                |
| ------ | ------------------------------------- | ------------------------------------------ |
| GET    | /health                               | Health check                               |
| GET    | /search?q=...&topic=...&limit=10      | Semantic search, optional topic filter     |
| GET    | /articles?topic=...&limit=20&offset=0 | List articles with metadata                |
| GET    | /articles/{id}                        | Single article with full content           |
| GET    | /topics                               | All topics with article counts             |
| POST   | /build                                | Trigger ingest pipeline (process manifest) |

## Web endpoints

Web UI is served by the same FastAPI process. All web routes are read-only.

| Method | Path                           | Description                                  |
| ------ | ------------------------------ | -------------------------------------------- |
| GET    | /                              | Main browse page (topics sidebar + article table + search) |
| GET    | /web/topics                    | Topic list fragment (HTMX)                   |
| GET    | /web/articles?topic=...        | Article list fragment (HTMX)                 |
| GET    | /web/search?q=...&topic=...    | Search results fragment (HTMX)               |
| GET    | /web/articles/{id}             | Full article detail page                     |

Article titles link to the original URL. A "details" link navigates to the Distillatron article page.

## UI

Two separate modalities sharing a common layout: topics sidebar + article table + search bar.

| Mode   | Command    | Framework        | Data access       | Build action |
| ------ | ---------- | ---------------- | ----------------- | ------------ |
| TUI    | `make tui` | Textual          | Direct imports    | Yes          |
| Web    | `make up`  | HTMX + Jinja2    | REST API          | No (read-only) |

### TUI screens

| Screen  | Layout | Navigation |
| ------- | ------ | ---------- |
| Browse  | Topics sidebar → article DataTable (Title, Topics, Source) + hidden search bar | `/` toggle search, click topic to filter, `Enter` view, `t` reset, `b` build, `q` quit |
| Article | Full markdown content, metadata, topic tags | `Esc` back, `o` open original URL |

### TUI data access

The TUI imports `distillatron.search`, `distillatron.db`, and `distillatron.embed` directly — no network calls for search. Web mode calls the REST API endpoints.

## Manifest format (`manifest.md`)

User-maintained bullet list of URLs. Each URL can have sub-items for processing status and
todos. The build system updates the manifest in-place after processing.

```
- [x] https://example.com/article
- [ ] https://example.com/another
- https://example.com/new-url
```

- New URLs have no sub-items or checkboxes (`[ ]`).
- `[ ]` means queued but not yet processed.
- `[x]` means done. Build skips these.

## Conventions

- **Project layout**: `src/distillatron/` for application code (includes `ui/` and `web/` subpackages),
  `tests/` for tests, `notebooks/` for Jupyter experimentation, `terraform/` for infra,
  `docker/` for Dockerfiles and compose config.
  `manifest.md` at project root (gitignored). `MANIFEST.md.example` committed as reference.
- **Dependency management**: `uv` for all dependency and virtual environment operations.
  `uv sync` to install, `uv add` to add deps, `uv lock` to regenerate lockfile. Check in `uv.lock`.
- **Formatting & linting**: `ruff` for both. Config in `pyproject.toml` under `[tool.ruff]`.
  `make lint` and `make fmt` targets.
- **Notebooks**: Jupyter notebooks live in `notebooks/`. Dev dependency: `ipykernel`.
  Register the kernel once with `make kernel` so VS Code can discover it as "Python 3.12 (distillatron)".
  In VS Code, open a `.ipynb` file and select this kernel from the picker. Or launch the browser
  interface with `make notebook`. Notebooks are for experimentation, not production code.
  Extract reusable logic into `src/distillatron/`.
- **Commit style**: conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`).
- **Testing**: pytest. Tests run inside Docker. `make test` target.
- **API design**: FastAPI best practices — dependency injection, Pydantic models for
  request/response, async handlers where I/O-bound.

## Constraints

- Local development runs entirely via `docker compose up` — no bare-metal services required.
- Manifest is the source of truth for URLs. No other URL entry point initially.
- Deployments must be reproducible via `terraform apply`.
- LanceDB mode: embedded (single-process), keep server/remote mode viable for later.
- State tracking: LanceDB query by URL (no separate lock file or database).
- API keys: all from environment variables, never committed. `.env.example` committed as template.
- Local embeddings by default (fastembed, ONNX runtime, no GPU). OpenAI embeddings available as fallback. Backend switchable via `EMBEDDING_BACKEND` env var.
- DeepSeek (deepseek-v4-flash) for topic classification.
- Firecrawl for article content scraping.

## Decision Log

| Date       | Decision                              | Rationale                                                                                                            | Trade-offs                                                                  |
| ---------- | ------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| 2026-06-20 | LanceDB as vector DB                  | Embedded mode keeps local dev simple (no separate service). Columnar format, S3-compatible for future cloud storage. | Less production-hardened vs Qdrant/Milvus; newer ecosystem.                 |
| 2026-06-20 | Python / FastAPI for web              | Strongest Python ML/vector library support. Async-first, Pydantic-native. Lightweight for API-first approach.        | Weaker typing than Go; GIL-bound for CPU work.                              |
| 2026-06-20 | Docker Compose local, Terraform cloud | Clean separation: compose for dev, terraform for infra. Terraform kept cloud-agnostic until deployment.              | Terraform cloud-agnostic adds abstraction overhead.                         |
| 2026-06-20 | Frontend deferred                     | Start API-first, no premature frontend commitment.                                                                   | May need to retrofit auth/sessions later.                                   |
| 2026-06-20 | uv for package management             | Fast (Rust), pip-compatible, native lockfile, venv management. One tool replaces pip/venv/pip-tools.                 | Newer than Poetry; smaller ecosystem of plugins.                            |
| 2026-06-20 | ruff for formatting/linting           | Fast (Rust), single tool replaces flake8/black/isort. Config lives in pyproject.toml.                                | Slightly fewer rules than flake8 plugin ecosystem.                          |
| 2026-06-20 | Jupyter for experimentation           | Iterative exploration of data, embeddings, and vector search before writing production code.                         | Notebooks drift from project deps if not managed.                           |
| 2026-06-20 | Markdown manifest as URL source       | Human-editable, simple format. Build updates in-place with processing status. Gitignored (personal URLs).            | Build modifies user's file — risk of merge conflicts. Must parse carefully. |
| 2026-06-20 | OpenAI text-embedding-3-small         | Good quality/cost ratio for semantic search. Standard OpenAI SDK.                                                    | External API dependency, per-token cost, latency.                           |
| 2026-06-20 | DeepSeek for topic classification     | OpenAI-compatible API, significantly cheaper than GPT-4o. Good classification quality.                               | Less enterprise support, potential availability risk.                       |
| 2026-06-20 | Firecrawl for article scraping        | Handles JavaScript pages, returns clean markdown. Already available in user's toolchain.                             | Requires API key. Trafilatura would be free but less capable.               |
| 2026-06-20 | LanceDB for dedup state tracking      | Query by URL before processing. No extra lock file. Matches source-of-truth pattern.                                 | Must ensure URL is always stored. No state if DB wiped.                     |
| 2026-06-20 | Open-ended topics with normalization  | LLM generates freeform tags, normalization pass merges synonyms. More organic than predefined taxonomy.              | Extra LLM call for normalization. Some inconsistency may persist.           |
| 2026-06-20 | CLI-only build trigger (`make build`) | Simplest for solo use. No auth needed on build endpoint.                                                             | No remote trigger. Must be on the machine.                                  |
| 2026-06-29 | fastembed for local embeddings        | OpenAI quota issues blocked development. fastembed uses ONNX, no GPU, sub-100MB download, 384d vectors, free, offline. | Lower quality than OpenAI embeddings. Must clear DB when switching backends (dimension mismatch). |
| 2026-06-29 | Textual for TUI                        | Native terminal UI with keyboard navigation, direct imports. Fast, no network needed for search.     | Terminal-only; no browser access from same code.                                  |
| 2026-06-29 | HTMX + Jinja2 for web UI               | Lightweight server-rendered web UI served by FastAPI. No JS framework build step. Read-only.          | Requires server round-trips; less interactive than SPA.                           |
| 2026-06-29 | Separate TUI and web code paths        | Textual's browser mode (textual-serve) felt like an emulation, not a useful web interface. Dedicated implementations give better UX in each modality. | Two codebases to maintain; shared layout spec keeps them aligned.                  |
| 2026-07-01 | Metadata title extraction              | Firecrawl V1 SDK returns `result.title` as None; actual title is in `result.metadata.title`. Fixed scrape.py to extract from metadata. | Relies on page metadata being present; falls back to URL if absent.                |
| 2026-06-29 | deepseek-v4-flash for classification  | User's preferred DeepSeek model. Faster and cheaper than GPT-4o.                                                       | Less tested in production than GPT-4o. Prompt compatibility may differ.      |
| 2026-06-29 | LanceModel for DB schema              | LanceDB 0.33+ requires `lancedb.pydantic.LanceModel` for table schema, not raw `pydantic.BaseModel`.                   | Tighter coupling to LanceDB's type system.                                   |
| 2026-06-29 | V1FirecrawlApp SDK                    | firecrawl-py 4.x renamed API: `FirecrawlApp` → `V1FirecrawlApp`. Response is Pydantic model, not dict.                 | SDK version lock-in. Breaking changes on major version bumps.                |

## Open Questions

- LanceDB embedded vs server mode for initial development? (embedded default; revisit if multi-process needed)
- Web server: uvicorn directly or behind Nginx/Caddy in the container?
- Observability stack: structlog? OpenTelemetry? Sentry?
- CI/CD: GitHub Actions or something else?
- Authentication: none for now, but what pattern when needed (JWT, OAuth2, API keys)?
- Notebook conventions: should notebooks use `uv run` kernel or installed ipykernel from venv?
- Manifest format extensibility: how to add future todo types without breaking the parser?
- UI data access: TUI uses direct imports, web calls REST API — resolved.
