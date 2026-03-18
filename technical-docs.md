# LLMfy - Technical Documentation

## Project Overview

LLMfy is a Python framework for developing applications with large language models (LLMs). It provides abstractions for multiple LLM providers (OpenAI, AWS Bedrock), workflow orchestration via FlowEngine, vector storage with FAISS, and utility functions for text processing.

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
│       ├── publish.yml         # PyPI publish workflow (triggered on v* tags)
│       └── release.yml         # GitHub release workflow (triggered on v* tags)
├── docs/                       # Documentation source files
├── llmfy/                      # Main package
│   ├── __init__.py             # Package exports
│   ├── py.typed                # PEP 561 type marker
│   ├── exception/              # Custom exception classes
│   ├── llmfy_core/             # Core LLM abstractions
│   │   ├── models/             # LLM model implementations (OpenAI, Bedrock)
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
| `numpy`            | numpy              | Numerical computing          |
| `faiss-cpu`        | faiss-cpu          | FAISS vector similarity      |
| `typing_extensions`| typing_extensions  | Backported typing features   |
| `redis`            | redis              | Redis checkpointer support   |
| `SQLAlchemy`       | SQLAlchemy         | SQL checkpointer support     |
| `all`              | All of the above   | Install all optional deps    |

### Development Dependencies

Defined in `[dependency-groups]` in `pyproject.toml`:

- **dev**: Runtime optional packages with pinned versions, python-dotenv, PyMySQL
- **docs**: mkdocs, mkdocs-material, mkdocstrings, and related plugins

---

## Building

```bash
# Build sdist and wheel
uv build

# Output is placed in dist/
ls dist/
# llmfy-0.4.13.tar.gz
# llmfy-0.4.13-py3-none-any.whl
```

The build uses **Hatchling** as the backend. Configuration in `pyproject.toml`:
- Only the `llmfy/` package is included in the wheel
- The `llmfy/test/` directory is excluded from distributions
- `py.typed` marker is included automatically

---

## Publishing to PyPI

### Automated (GitHub Actions)

Publishing is fully automated via `.github/workflows/publish.yml`:

1. Create and push a version tag:
   ```bash
   git tag v0.4.13
   git push origin v0.4.13
   ```

2. The workflow automatically:
   - Installs UV
   - Builds the package with `uv build`
   - Publishes to PyPI with `uv publish`

**Required secret**: `PYPI_API_TOKEN` must be configured in the GitHub repository settings.

### Manual

```bash
# Build
uv build

# Publish (requires UV_PUBLISH_TOKEN env var or --token flag)
UV_PUBLISH_TOKEN=your_token uv publish
```

---

## GitHub Workflows

### Publish (`publish.yml`)

- **Trigger**: Push tag matching `v*`
- **Action**: Builds and publishes to PyPI using UV
- **Secret**: `PYPI_API_TOKEN`

### Release (`release.yml`)

- **Trigger**: Push tag matching `v*` or manual dispatch
- **Action**: Creates a GitHub Release with auto-generated changelog

### Release Process

The version is **automatically derived from git tags** using `hatch-vcs`. No need to manually edit any version field.

```bash
# 1. Create and push tag
git tag v0.4.14
git push origin main --tags
```

Both workflows trigger on the tag push — the package is built with the version from the tag, published to PyPI, and a GitHub Release is created.

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
| Exactly on tag `v0.4.14` | `0.4.14` |
| 3 commits after `v0.4.14` | `0.4.15.dev3+g<commit>` |
| No tags in history | Error (build fails) |

### Generated File

At build time, `hatch-vcs` generates `llmfy/_version.py` containing the resolved version. This file is:
- **Included** in the built wheel (so `from llmfy import __version__` works at runtime)
- **Gitignored** (auto-generated, not tracked in source control)

### Access Version at Runtime

```python
from llmfy import __version__
print(__version__)  # e.g., "0.4.14"
```

### Release Flow

```bash
# 1. Create a version tag
git tag v0.4.14

# 2. Push the tag (triggers publish + release workflows)
git push origin main --tags
```

The tag `v0.4.14` is automatically stripped of the `v` prefix, so the package is published to PyPI as version `0.4.14`.
