---
title: PII Guard
description: Detect, mask, and reversibly tokenize PII using PIIGuard.
---

# PII Guard

`PIIGuard` scans text and returns a structured result. Most PII types use compiled regex and need no external dependencies; `PERSON_NAME` and `ADDRESS` additionally use an optional spaCy NER model, loaded lazily on first use (see [NER-backed Types](#ner-backed-types-person_name-address)). `PIIGuard` keeps no internal state between calls — every method call is self-contained.

## Setup

```python linenums="1"
from llmfy import PIIGuard, PIIStrategy, PIIType
```

## Supported PII Types

| PIIType | Example match | Notes |
|---|---|---|
| `EMAIL` | `john@example.com` | |
| `PHONE_NUMBER` | `(555) 123-4567`, `+628987654321` | Compact international and US/`+1` formats |
| `SSN` | `123-45-6789` | |
| `NIK` | `3171012501990002` | Indonesian national ID — plain 16 digits |
| `CREDIT_CARD` | `4111 1111 1111 1111` | |
| `IP_ADDRESS` | `192.168.1.1` | |
| `DATE_OF_BIRTH` | `01/15/1990`, `2024-03-15`, `January 1, 2000` | |
| `PASSPORT_NUMBER` | `AB1234567`, `C1234567` | 1-2 letters + 6-9 digits — also covers the Indonesian format (1 letter + 7 digits) |
| `PERSON_NAME` | `Budi Santoso` | Requires the optional `xx_ent_pii_sm` spaCy NER model — see [NER-backed Types](#ner-backed-types-person_name-address) |
| `ADDRESS` | `Jl. Merdeka No. 10, Jakarta` | Requires the optional `xx_ent_pii_sm` spaCy NER model — see [NER-backed Types](#ner-backed-types-person_name-address) |

!!! note "NIK also matches Kartu Keluarga (KK) numbers"
    There's no separate `KK_NUMBER` type — Indonesian family card (Kartu Keluarga) numbers use the exact same plain 16-digit format as NIK, with no structural way to tell them apart by regex alone. Both are detected as `NIK`.

## Strategies

`PIIGuard` has four strategies, all controlled by a single `strategy` parameter — there is no second "mask style" parameter to combine with it.

| Strategy | Reversible? | Placeholder | Example |
|---|---|---|---|
| `PARTIAL` | No | First 2 chars of the value + `*` | `jo*` |
| `MASK` | No (by convention) | Numbered label, unique per value | `[EMAIL_1]`, `[EMAIL_2]` |
| `REDACT` | No | Generic, same for every value | `[REDACTED]` |
| `TOKENIZE` (default) | Yes | Numbered label, unique per value (same format as `MASK`) | `[EMAIL_1]`, `[EMAIL_2]` |

### PARTIAL

```python linenums="1"
guard = PIIGuard(strategy=PIIStrategy.PARTIAL)
result = guard.detect("Email: john@example.com, SSN: 123-45-6789")

print(result.processed_text)
# "Email: jo**************, SSN: 12*********"
```

### MASK

Each distinct value gets its own numbered placeholder — two different emails never collapse into the same label, so downstream consumers (including an LLM) can still tell them apart.

```python linenums="1"
guard = PIIGuard(strategy=PIIStrategy.MASK)
result = guard.detect("Email: john@example.com, SSN: 123-45-6789")

print(result.processed_text)
# "Email: [EMAIL_1], SSN: [SSN_1]"
```

If the same value repeats in the text, it reuses the same placeholder instead of incrementing:

```python linenums="1"
result = guard.detect(
    "Primary: alice@example.com, Secondary: bob@example.com, "
    "CC: carol@example.com, Repeat: alice@example.com"
)
print(result.processed_text)
# "Primary: [EMAIL_1], Secondary: [EMAIL_2], CC: [EMAIL_3], Repeat: [EMAIL_1]"
```

`MASK` is intended as one-way: even though the returned `detections` technically retain the original value (see [Working with Results](#working-with-results)), the convention is that callers using `MASK` don't hold on to that mapping for later restoration. Use `TOKENIZE` when you actually intend to restore.

### REDACT

```python linenums="1"
guard = PIIGuard(strategy=PIIStrategy.REDACT)
result = guard.detect("Email: john@example.com, SSN: 123-45-6789")

print(result.processed_text)
# "Email: [REDACTED], SSN: [REDACTED]"
```

Every value shares the same `[REDACTED]` placeholder, so this strategy is **not reversible** — `restore()` cannot tell which original value a given `[REDACTED]` occurrence corresponds to once there is more than one.

### TOKENIZE

Same placeholder format as `MASK` (numbered, unique per value), but this is the strategy meant to be paired with `restore()`. See [Reversible Masking with TOKENIZE](#reversible-masking-with-tokenize) below.

## Reversible Masking with TOKENIZE

`PIIGuard` never stores PII values itself — there is no internal vault or cache. `detect()` already returns the original value alongside each placeholder in `result.detections`; the caller is responsible for holding on to that list and passing it back into `restore()` whenever they want the original values back.

```python linenums="1"
guard = PIIGuard(strategy=PIIStrategy.TOKENIZE)
result = guard.detect("Contact john.doe@example.com or backup alice@example.com")

print(result.processed_text)
# "Contact [EMAIL_1] or backup [EMAIL_2]"

# The caller holds on to result.detections themselves — PIIGuard stores nothing.
restored = guard.restore(result.processed_text, result.detections)
print(restored)
# "Contact john.doe@example.com or backup alice@example.com"
print(restored == result.original_text)  # True
```

`restore()` doesn't require the exact `processed_text` that was returned — it works on **any** text that still contains the same placeholders. This is the common real-world case: an LLM echoes a placeholder back inside a brand-new sentence, and you restore it before showing the response to the user.

```python linenums="1"
result = guard.detect("My email is john.doe@example.com")
# result.processed_text == "My email is [EMAIL_1]"

# Simulate a downstream system (e.g. an LLM) echoing the token back inside new text.
llm_reply = f"Sure, I'll send the confirmation to {result.detections[0].placeholder} shortly."

restored_reply = guard.restore(llm_reply, result.detections)
print(restored_reply)
# "Sure, I'll send the confirmation to john.doe@example.com shortly."
```

Placeholders in the input text that aren't present in the given `detections` are left untouched — `restore()` never raises for unknown placeholders.

!!! warning "Don't use restore() with REDACT"
    `REDACT` placeholders (`[REDACTED]`) aren't unique per value, so `restore()` can't disambiguate which original value a given occurrence maps to once there's more than one PII value in the text. Only use `restore()` with `TOKENIZE` results (or `MASK`, though that's against its one-way convention).

## Filtering Types

Pass a `types` list to detect only specific PII categories. All other types are ignored.

```python linenums="1"
guard = PIIGuard(
    strategy=PIIStrategy.PARTIAL,
    types=[PIIType.EMAIL, PIIType.PHONE_NUMBER],
)
result = guard.detect(
    "Reach me at alice@corp.com or (212) 555-0100. SSN: 111-22-3333 is untouched."
)

print(result.processed_text)
# "Reach me at al************ or (2************. SSN: 111-22-3333 is untouched."
```

### Excluding a few types

`types` is an *include* list — using it to drop just one or two types means
enumerating every other `PIIType` yourself. Use `exclude_types` instead to
keep everything except the types you name:

```python linenums="1"
guard = PIIGuard(
    strategy=PIIStrategy.MASK,
    exclude_types=[PIIType.SSN],
)
result = guard.detect("Email: jane@test.org, SSN: 123-45-6789")

print(result.processed_text)
# "Email: [EMAIL_1], SSN: 123-45-6789"
```

`types` and `exclude_types` are mutually exclusive — passing both raises
`ValueError`.

## Scanning Without Replacing

`scan()` returns all detections sorted by character position without modifying the text.

```python linenums="1"
guard = PIIGuard()
findings = guard.scan("admin@corp.com logged in from 10.0.0.1 on 2024-03-15")

for f in findings:
    print(f.pii_type, f.value, f.start, f.end)
# EMAIL         admin@corp.com  0  14
# IP_ADDRESS    10.0.0.1        30  38
# DATE_OF_BIRTH 2024-03-15      42  52
```

## Working with Results

`PIIDetectionResult` is a Pydantic model — call `model_dump()` to serialize it.

```python linenums="1"
guard = PIIGuard(strategy=PIIStrategy.PARTIAL)
result = guard.detect("Call me at 555-867-5309")

print(result.has_pii)          # True
print(result.strategy)         # partial
print(result.original_text)    # "Call me at 555-867-5309"
print(result.processed_text)   # "Call me at 55*********"

for d in result.detections:
    print(d.pii_type)          # PHONE_NUMBER
    print(d.value)              # 555-867-5309
    print(d.start, d.end)       # 11 23
    print(d.placeholder)        # 55*********
```

## Phone Number Formats

`PHONE_NUMBER` supports both compact international and US/`+1` formats.

```python linenums="1"
guard = PIIGuard(strategy=PIIStrategy.MASK, types=[PIIType.PHONE_NUMBER])

texts = [
    "+628987654321",    # compact international
    "+1 800 555-9876",  # +1 with spaces
    "(555) 123-4567",   # US with parens
    "555-123-4567",     # US dashes
]

for t in texts:
    r = guard.detect(t)
    print(r.processed_text)
# [PHONE_NUMBER_1]
# [PHONE_NUMBER_1]
# [PHONE_NUMBER_1]
# [PHONE_NUMBER_1]
```

## Custom Types

Pass a `custom_types` dict mapping a **type name** (str) to a **regex pattern** (str or compiled `re.Pattern`) to define domain-specific PII — employee IDs, internal codes, API tokens, or any regex you need. The type name becomes the placeholder label for `MASK`/`TOKENIZE`, and the first two characters are used for `PARTIAL`.

### Combined with all built-in types by default

If you don't pass `types`, **all** built-in `PIIType`s stay active alongside your custom patterns — you don't need to opt back into them.

```python linenums="1"
guard = PIIGuard(
    strategy=PIIStrategy.PARTIAL,
    custom_types={
        "EMPLOYEE_ID": r"EMP-\d{6}",
        "PROJECT_CODE": r"PRJ-[A-Z]{3}",
    },
)
result = guard.detect(
    "Employee EMP-001234 is on project PRJ-ABC and emailed john@corp.com"
)

print(result.processed_text)
# "Employee EM******** is on project PR***** and emailed jo***********"
print([str(d.pii_type) for d in result.detections])
# ['EMPLOYEE_ID', 'PROJECT_CODE', 'EMAIL']
```

### Combined with a filtered subset of built-in types

Pass `types` to narrow which built-ins run alongside the custom patterns.

```python linenums="1"
guard = PIIGuard(
    types=[PIIType.EMAIL, PIIType.PHONE_NUMBER],
    custom_types={"EMPLOYEE_ID": r"EMP-\d{6}"},
)
result = guard.detect(
    "Staff EMP-007890 reached at carol@example.com or +628987654321"
)

print([str(d.pii_type) for d in result.detections])
# ['EMPLOYEE_ID', 'EMAIL', 'PHONE_NUMBER']
```

### Disabling all built-in types

```python linenums="1"
guard = PIIGuard(
    strategy=PIIStrategy.REDACT,
    types=[],
    custom_types={"EMPLOYEE_ID": r"EMP-\d{6}"},
)
result = guard.detect("ID: EMP-001234, Email: bob@example.com")

print(result.processed_text)
# "ID: [REDACTED], Email: bob@example.com"
```

!!! note
    `types=[]` disables all built-in PII types. Only the custom patterns run.

### Overriding a built-in type

If a custom type name matches a built-in `PIIType` value (e.g. `"EMAIL"`), the custom pattern **replaces** the built-in one entirely — the built-in pattern is suppressed for that name.

```python linenums="1"
# Only matches custom-*@*.com — standard email addresses are left alone
guard = PIIGuard(custom_types={"EMAIL": r"custom-\w+@\w+\.com"})
result = guard.detect("Regular john@example.com and custom-user@corp.com")

print(result.processed_text)
# "Regular john@example.com and [EMAIL_1]"
```

Overriding one built-in type leaves the rest active:

```python linenums="1"
# PHONE_NUMBER now only matches +62 (Indonesian) numbers
guard = PIIGuard(custom_types={"PHONE_NUMBER": r"\+62\d{9,12}"})
result = guard.detect("Call +628987654321 or (555) 123-4567, email bob@test.com")

print(result.processed_text)
# "Call [PHONE_NUMBER_1] or (555) 123-4567, email [EMAIL_1]"
```

`(555) 123-4567` is left untouched because the built-in `PHONE_NUMBER` pattern was suppressed, and the custom pattern doesn't match it.

### Custom types are fully TOKENIZE-compatible

`restore()` doesn't distinguish between built-in and custom types — a custom type's `detections` restore exactly the same way.

```python linenums="1"
guard = PIIGuard(
    strategy=PIIStrategy.TOKENIZE,
    custom_types={"EMPLOYEE_ID": r"EMP-\d{6}"},
)
result = guard.detect("Employee EMP-001234, email john@corp.com")

restored = guard.restore(result.processed_text, result.detections)
print(restored == result.original_text)  # True
```

## NER-backed Types (PERSON_NAME / ADDRESS)

`PERSON_NAME` and `ADDRESS` can't be reliably matched by regex, so they're detected via the [`xx_ent_pii_sm`](https://github.com/irufano/spacy_ner_pii) spaCy NER model instead of `PIIGuard`'s regex patterns. Install it:

=== "Using UV"
    ```sh
    uv add "llmfy[spacy]"
    uv add https://github.com/irufano/spacy_ner_pii/releases/download/v0.1.0/xx_ent_pii_sm-0.1.0-py3-none-any.whl
    ```

=== "Using pip"
    ```sh
    pip install "llmfy[spacy]"
    pip install https://github.com/irufano/spacy_ner_pii/releases/download/v0.1.0/xx_ent_pii_sm-0.1.0-py3-none-any.whl
    ```

The model isn't published to PyPI, so it can't be a `pyproject.toml` extra — the second command installs it directly from the GitHub release wheel.

The pipeline loads lazily: it's only loaded the first time `scan()`/`detect()` actually runs with `PERSON_NAME` or `ADDRESS` active, never at `PIIGuard()` construction or import time. If the model isn't installed and one of these types is active, `PIIGuard` raises `LLMfyException` with an install hint at that first call.

```python linenums="1"
guard = PIIGuard(strategy=PIIStrategy.MASK)
result = guard.detect("Budi Santoso tinggal di Jl. Merdeka No. 10, Jakarta.")

print(result.processed_text)
# "[PERSON_NAME_1] tinggal di [ADDRESS_1]."
```

!!! warning "Breaking change: default PIIGuard() now requires this model"
    `types=None` (the default) detects **every** `PIIType`, including `PERSON_NAME` and `ADDRESS` — so a bare `PIIGuard()` now requires the spaCy model once you call `scan()`/`detect()`, where earlier versions were regex-only with no dependency. Pass `exclude_types=[PIIType.PERSON_NAME, PIIType.ADDRESS]` to keep the old zero-dependency behavior:
    ```python linenums="1"
    guard = PIIGuard(exclude_types=[PIIType.PERSON_NAME, PIIType.ADDRESS])
    ```

### Production Tips

**Don't install the wheel from GitHub at deploy/runtime.** Pulling `https://github.com/.../xx_ent_pii_sm-0.1.0-py3-none-any.whl` during a production build or on server start makes every deploy depend on GitHub being reachable — if it's down, rate-limited, or the release is moved, your deploy or a cold-start fails. Instead, fetch the wheel once and vendor it:

=== "Copy the wheel to the server"
    ```sh
    # once, from a machine with internet access
    scp xx_ent_pii_sm-0.1.0-py3-none-any.whl user@server:/opt/models/

    # on the server — no GitHub access needed
    pip install /opt/models/xx_ent_pii_sm-0.1.0-py3-none-any.whl
    ```

=== "Multi-stage Docker build"
    ```dockerfile
    FROM python:3.11 AS builder
    RUN pip install --target=/deps \
        "xx_ent_pii_sm @ https://github.com/irufano/spacy_ner_pii/releases/download/v0.1.0/xx_ent_pii_sm-0.1.0-py3-none-any.whl"

    FROM python:3.11-slim
    COPY --from=builder /deps /usr/local/lib/python3.11/site-packages/
    ```
    The final image never touches GitHub — the model ships baked into the image layer.

=== "uv project dependency"
    ```sh
    uv add https://github.com/irufano/spacy_ner_pii/releases/download/v0.1.0/xx_ent_pii_sm-0.1.0-py3-none-any.whl
    ```
    Pins the wheel (with hash) in `pyproject.toml`/`uv.lock`, so `uv sync --frozen` installs a reproducible, known-good version — still fetches over the network unless the wheel is also mirrored to an internal index/artifact store.

Other things worth doing before relying on this in production:

- **Pin the exact version** (`v0.1.0`, not a moving "latest" link) so re-deploys and rollbacks stay reproducible.
- **Warm up the pipeline at startup**, not on the first user request — call `PIIGuard(types=[PIIType.PERSON_NAME]).scan("")` once in your app's startup/health-check hook so the (comparatively slow) model load doesn't add latency to the first real request.
- **Budget memory per worker process.** The pipeline is cached at class level (loaded once per process, shared across `PIIGuard` instances), but each worker/replica in a multi-process deployment (Gunicorn workers, K8s pods, serverless instances) loads its own copy — account for that in memory limits and per-instance cold-start time.
- **Validate against real data before trusting it for compliance.** The model card reports high precision/recall, but it was trained on synthetic, templated sentences — real-world phrasing, typos, and mixed-language text may perform worse. For a PII guardrail, a missed detection (false negative) is the dangerous failure mode, so test against a representative sample of your own production text before treating `PERSON_NAME`/`ADDRESS` detection as a compliance guarantee rather than a best-effort filter.

## Constructor Reference

```python
PIIGuard(
    strategy: PIIStrategy = PIIStrategy.TOKENIZE,
    types: list[PIIType] | None = None,          # None = all built-in types
    exclude_types: list[PIIType] | None = None,  # mutually exclusive with `types`
    custom_types: dict[str, str | re.Pattern] | None = None,
)
```

## Method Reference

| Method | Description |
|---|---|
| `detect(text)` | Returns `PIIDetectionResult` with PII replaced in `processed_text` |
| `scan(text)` | Returns `List[PIIDetection]` — finds PII without modifying the text |
| `restore(text, detections)` | Substitutes placeholders in `text` back to their original values, using a previously returned `detections` list |
