# Contributing

## Commit message format

Commit subjects follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <short summary>

[optional body]
```

- `type` is one of: `feat`, `fix`, `refactor`, `chore`, `ci`, `docs`, `test`.
- For a breaking change, prefix the subject with `[breaking-changes]`, e.g. `[breaking-changes] refactor: consolidate thinking config`.
- Keep the summary in the imperative mood (e.g. "add", not "added"/"adds").
- The release workflow copies each commit's subject and body verbatim into the GitHub release changelog, so write both to be read standalone (see `.github/workflows/release.yml`).

## Version bump rules (automatic tagging)

Every push to `main` is scanned by `.github/workflows/auto-tag.yml`, which tags a new release automatically — no manual `git tag` needed. The bump is decided per commit subject, in this precedence order (highest across all new commits wins):

| Commit subject | Bump |
|---|---|
| `[breaking-changes] <type>: ...` **or** `<type>!: ...` / `<type>(scope)!: ...` | **MAJOR** |
| `feat: ...` (no breaking marker) | **MINOR** |
| `fix: ...` (no breaking marker) | **PATCH** |
| `refactor:`, `chore:`, `ci:`, `docs:`, `test:` alone | no release (bundled into the next qualifying commit) |

A breaking marker always forces MAJOR regardless of type — use it deliberately when a `feat` or `fix` must ship as a major version, e.g. `[breaking-changes] feat: ...` or `feat!: ...`, both equivalent.

## Build package

```sh
uv build
```

## Manual / backfill release

Tagging is automatic (see above). To manually cut or re-run a release, use the `workflow_dispatch` trigger on `release.yml` (GitHub Actions UI → "Release & Publish" → "Run workflow", tag input `vX.Y.Z`) instead of pushing a tag by hand.

## After deploy on local

After CI creates or moves the tag, your local tag ref may be stale. To sync:

```sh
git fetch --tags --force
```

The --force flag is needed because git fetch --tags alone won't update tags that already exist locally.

## Package Development on local

```sh
uv sync --group dev --group docs
```

or

```sh
uv sync --all-groups
```

## Check Lints

```sh
uvx ruff check --statistics . 2>&1 | tail -60
```

## Mkdocs run on local

```sh
uv sync --group docs
```

```sh
# Serve on local
mkdocs serve

# Build docs
mkdocs build
```
