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
     ├── OpenAI ───────────► embed content → vector
     ├── DeepSeek ─────────► classify → raw topics → normalize → final topics
     ├── LanceDB ──────────► store: url, title, content, embedding, topics, source, scraped_at
     └── manifest.md ──────► update: [x] Indexed + timestamp under each processed URL
     │
     ▼
FastAPI API              ← GET /search, /articles, /articles/{id}, /topics; POST /build
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
| Embeddings         | OpenAI text-embedding-3-small | Good quality/cost balance. OPENAI_API_KEY from env.                         |
| Classification     | DeepSeek (via OpenAI SDK)     | OpenAI-compatible endpoint. Cheaper than GPT-4o. DEEPSEEK_API_KEY from env. |
| Scraping           | Firecrawl SDK                 | Handles JS pages, returns clean markdown. FIRECRAWL_API_KEY from env.       |
| Notebooks          | Jupyter                       | Iterative experimentation, shared kernel with project venv                  |
| Container runtime  | Docker + Docker Compose       | Local dev mirrors production topology                                       |
| Infrastructure     | Terraform                     | Cloud-agnostic modules, provider chosen at deploy time                      |
| Frontend           | Deferred                      | Start API-first, decide later                                               |
| Cloud              | Unspecified                   | Terraform written agnostic; AWS or GCP likely candidates                    |

## Source modules

| Module            | Purpose                                                                      |
| ----------------- | ---------------------------------------------------------------------------- |
| `src/db.py`       | LanceDB connection, `articles` table schema, `get_db()`                      |
| `src/manifest.py` | Parse `manifest.md`: extract URLs with status. Update manifest in-place.     |
| `src/scrape.py`   | Firecrawl SDK: URL → title + markdown content                                |
| `src/embed.py`    | OpenAI: text → vector (text-embedding-3-small)                               |
| `src/classify.py` | DeepSeek: content → raw topic tags → normalize → final topics                |
| `src/ingest.py`   | Pipeline orchestrator: manifest → scrape → embed → classify → store → update |
| `src/search.py`   | Embed query → ANN search LanceDB → ranked results                            |
| `src/routes.py`   | FastAPI router: /search, /articles, /articles/{id}, /topics, /build          |
| `src/main.py`     | FastAPI app entry point, lifespan, router registration                       |

## LanceDB schema — `articles` table

| Column     | Type        | Description                          |
| ---------- | ----------- | ------------------------------------ |
| id         | str         | UUID, primary key                    |
| url        | str         | Article URL (unique, used for dedup) |
| title      | str         | Article title                        |
| content    | str         | Full markdown content                |
| embedding  | list[float] | Vector from OpenAI embedding         |
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

- **Project layout**: `src/` for application code, `tests/` for tests, `notebooks/` for Jupyter
  experimentation, `terraform/` for infra, `docker/` for Dockerfiles and compose config.
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
- OpenAI for embeddings (text-embedding-3-small). DeepSeek for topic classification.
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

## Open Questions

- LanceDB embedded vs server mode for initial development? (embedded default; revisit if multi-process needed)
- Web server: uvicorn directly or behind Nginx/Caddy in the container?
- Observability stack: structlog? OpenTelemetry? Sentry?
- CI/CD: GitHub Actions or something else?
- Authentication: none for now, but what pattern when needed (JWT, OAuth2, API keys)?
- Notebook conventions: should notebooks use `uv run` kernel or installed ipykernel from venv?
- Topic normalization strategy: how to merge synonyms (e.g., "AI" / "artificial intelligence")? Static mapping? Second LLM pass? Embedding similarity?
- Manifest format extensibility: how to add future todo types without breaking the parser?
- DeepSeek model: which specific model (deepseek-chat, deepseek-reasoner)?
