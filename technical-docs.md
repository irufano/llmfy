# LLMfy - Technical Documentation

## Project Overview

LLMfy is a Python framework for developing applications with large language models (LLMs). It provides abstractions for multiple LLM providers (OpenAI, AWS Bedrock, Google AI), workflow orchestration via FlowEngine, vector storage with FAISS, and utility functions for text processing.

- **Python**: >= 3.11
- **Package Manager**: [UV](https://docs.astral.sh/uv/)
- **Build Backend**: [Hatchling](https://hatch.pypa.io/)
- **Documentation**: [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)
- **License**: MIT

---

## Project Structure

```
llmfy/
├── pyproject.toml              # Project configuration, dependencies, build settings
├── README.md                   # Project readme
├── LICENSE                     # MIT license
├── mkdocs.yml                  # MkDocs configuration
├── .readthedocs.yaml           # ReadTheDocs build configuration
├── .github/
│   └── workflows/
│       └── release.yml         # Release & Publish workflow (triggered on v* tags)
├── docs/                       # Documentation source files
├── llmfy/                      # Main package
│   ├── __init__.py             # Package exports
│   ├── py.typed                # PEP 561 type marker
│   ├── exception/              # Custom exception classes
│   ├── llmfy_core/             # Core LLM abstractions
│   │   ├── models/             # LLM model implementations (OpenAI, Bedrock, Google AI)
│   │   │   ├── google/         # Google AI (Gemini) model, config, usage, pricing
│   │   ├── embeddings/         # Embedding models
│   │   ├── messages/           # Message handling
│   │   ├── tools/              # Tool definitions and registry
│   │   ├── responses/          # Response types
│   │   └── usage/              # Usage tracking
│   ├── flow_engine/            # Workflow orchestration engine
│   │   ├── node/               # Node implementations
│   │   ├── edge/               # Edge definitions
│   │   ├── state/              # State management
│   │   ├── stream/             # Streaming support
│   │   ├── checkpointer/       # State persistence (InMemory, Redis, SQL)
│   │   ├── helper/             # Helper utilities
│   │   └── visualizer/         # Workflow visualization
│   ├── vector_store/           # Vector store (FAISS)
│   └── llmfy_utils/            # Utilities (chunking, logging, text processing)
└── site/                       # Generated documentation (not committed)
```

---

## Development Setup

### Prerequisites

- Python 3.11 or higher
- [UV](https://docs.astral.sh/uv/) package manager

### Install UV

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via Homebrew
brew install uv
```

### Initialize Project

```bash
# Install all dependencies (core + dev + docs)
uv sync --all-groups

# Install only core dependencies
uv sync

# Install with specific dependency group
uv sync --group dev
uv sync --group docs
```

### Running Scripts

```bash
# Run any Python script through uv
uv run python your_script.py

# Run mkdocs locally
uv run mkdocs serve
```

---

## Dependencies

### Core (Runtime)

| Package   | Description                    |
|-----------|--------------------------------|
| pydantic  | Data validation and settings   |

### Optional Extras

Install with `pip install llmfy[extra_name]` or `pip install llmfy[all]`.

| Extra              | Package            | Description                  |
|--------------------|--------------------|------------------------------|
| `openai`           | openai             | OpenAI API client            |
| `boto3`            | boto3              | AWS SDK (Bedrock)            |
| `google-genai`     | google-genai       | Google AI (Gemini) client    |
| `numpy`            | numpy              | Numerical computing          |
| `faiss-cpu`        | faiss-cpu          | FAISS vector similarity      |
| `typing_extensions`| typing_extensions  | Backported typing features   |
| `redis`            | redis              | Redis checkpointer support   |
| `SQLAlchemy`       | SQLAlchemy         | SQL checkpointer support     |
| `all`              | All of the above   | Install all optional deps    |

### Development Dependencies

Defined in `[dependency-groups]` in `pyproject.toml`:

- **dev**: Runtime optional packages with pinned versions, python-dotenv, PyMySQL, google-genai
- **docs**: mkdocs, mkdocs-material, mkdocstrings, and related plugins

---

## Exception Handling

LLMfy maps provider-specific API errors to a unified exception hierarchy under `llmfy.exception`.

### Base Exception

All exceptions inherit from `LLMfyException`:

```python
from llmfy import LLMfyException
```

| Attribute    | Description                              |
|--------------|------------------------------------------|
| `message`    | Human-readable error message             |
| `status_code`| HTTP status code (if applicable)         |
| `raw_error`  | Original provider error payload          |
| `provider`   | Provider name (`openai`, `bedrock`, `google`) |

### Exception Classes

| Exception                  | Typical HTTP Code | When Raised                         |
|----------------------------|-------------------|-------------------------------------|
| `AuthenticationException`  | 401               | Invalid or missing API key          |
| `PermissionDeniedException`| 403               | Insufficient permissions            |
| `InvalidRequestException`  | 400               | Malformed request or invalid params |
| `ModelNotFoundException`   | 404               | Model ID not found                  |
| `RateLimitException`       | 429               | Rate limit exceeded                 |
| `QuotaExceededException`   | 429 / 402         | Quota or billing limit exceeded     |
| `ContentFilterException`   | 400 / 451         | Content blocked by safety filters   |
| `ModelErrorException`      | 500               | Internal model error                |
| `ServiceUnavailableException` | 503            | Provider service down or overloaded |
| `TimeoutException`         | 408 / 504         | Request timed out                   |

### Provider Error Handlers

Each provider has a dedicated handler that translates native errors:

| Function               | Provider   |
|------------------------|------------|
| `handle_openai_error`  | OpenAI     |
| `handle_bedrock_error` | AWS Bedrock|
| `handle_google_error`  | Google AI  |

### Usage

```python
from llmfy import LLMfy, LLMfyException, RateLimitException

try:
    response = llm.generate(messages)
except RateLimitException as e:
    print(f"Rate limited: {e.message} (status={e.status_code})")
except LLMfyException as e:
    print(f"LLM error [{e.provider}]: {e.message}")
```

---

## Building

```bash
# Build sdist and wheel
uv build

# Output is placed in dist/
ls dist/
# llmfy-0.4.21.tar.gz
# llmfy-0.4.21-py3-none-any.whl
```

The build uses **Hatchling** as the backend. Configuration in `pyproject.toml`:
- Only the `llmfy/` package is included in the wheel
- The `llmfy/test/` directory is excluded from distributions
- `py.typed` marker is included automatically

---

## Publishing to PyPI

### Automated (GitHub Actions)

Publishing is fully automated via `.github/workflows/release.yml`. See [GitHub Workflow](#github-workflow) for details.

1. Create and push a version tag:
   ```bash
   git tag v0.4.22
   git push origin v0.4.22
   ```

2. The workflow automatically handles version badge updates, PyPI publishing, and GitHub Release creation in order.

**Required secret**: `PYPI_API_TOKEN` must be configured in the GitHub repository settings.

### Manual

```bash
# Build
uv build

# Publish (requires UV_PUBLISH_TOKEN env var or --token flag)
UV_PUBLISH_TOKEN=your_token uv publish
```

---

## GitHub Workflow

All release automation is consolidated in a single workflow: `.github/workflows/release.yml`.

### Release & Publish (`release.yml`)

- **Trigger**: Push tag matching `v*` or manual dispatch
- **Secret**: `PYPI_API_TOKEN`

The workflow runs three jobs **in sequence** to ensure version badges are updated before publishing:

| Job | Depends On | Action |
|-----|-----------|--------|
| **1. update-version** | — | Updates hardcoded version badges in `README.md` and `docs/index.md`, commits and pushes to `main` |
| **2. publish** | update-version | Checks out the updated commit, builds with `uv build`, publishes to PyPI with `uv publish` |
| **3. create-release** | update-version, publish | Generates changelog from git history, creates GitHub Release |

This ensures:
- PyPI package is built from the commit with updated version badges
- ReadTheDocs picks up the push to `main` with correct badges in `docs/index.md`
- GitHub Release is only created after successful publish

### Release Process

The version is **automatically derived from git tags** using `hatch-vcs`. No need to manually edit any version field.

```bash
# 1. Create and push tag
git tag v0.4.22
git push origin v0.4.22
```

### Version Badges

Both `README.md` and `docs/index.md` contain two version badges:

- **Current version** (hardcoded, green `31CA9C`) — shows the version at the time of that commit. Automatically updated by the `update-version` job on each tag push via `sed` replacement.
- **Latest version** (dynamic from PyPI, `691DC6`) — always shows the latest published version on PyPI.

This means when viewing an old commit on GitHub, you can see both the version at that point in time and the current latest version.

**Files auto-updated by CI:**
- `README.md`
- `docs/index.md`

---

## Documentation

Documentation is built with MkDocs and the Material theme.

```bash
# Serve docs locally (hot-reload)
uv run mkdocs serve

# Build static docs
uv run mkdocs build
```

Documentation is also hosted on ReadTheDocs. The `.readthedocs.yaml` configuration uses UV to install docs dependencies and build the site.

---

## Version Management

The package version is **automatically derived from git tags** — no manual version editing is needed.

### How It Works

This project uses [`hatch-vcs`](https://github.com/ofek/hatch-vcs) to read the version from git tags at build time. The relevant configuration in `pyproject.toml`:

```toml
[build-system]
requires = ["hatchling", "hatch-vcs"]

[project]
dynamic = ["version"]

[tool.hatch.version]
source = "vcs"
tag-pattern = "v(?P<version>.*)"

[tool.hatch.build.hooks.vcs]
version-file = "llmfy/_version.py"
```

### Version Resolution

| Git State | Resolved Version |
|-----------|-----------------|
| Exactly on tag `v0.4.21` | `0.4.21` |
| 3 commits after `v0.4.21` | `0.4.22.dev3+g<commit>` |
| No tags in history | Error (build fails) |

### Generated File

At build time, `hatch-vcs` generates `llmfy/_version.py` containing the resolved version. This file is:
- **Included** in the built wheel (so `from llmfy import __version__` works at runtime)
- **Gitignored** (auto-generated, not tracked in source control)

### Access Version at Runtime

```python
from llmfy import __version__
print(__version__)  # e.g., "0.4.21"
```

### Release Flow

```bash
# 1. Create a version tag
git tag v0.4.22

# 2. Push the tag (triggers release.yml workflow)
git push origin v0.4.22
```

The tag `v` prefix is automatically stripped, so the package is published to PyPI as the bare version number (e.g., `v0.4.22` → `0.4.22`).
