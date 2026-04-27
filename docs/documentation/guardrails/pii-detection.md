---
title: PII Detection
description: Detect and replace PII using strategies and mask styles.
---

# PII Detection

`PIIDetector` scans text with compiled regex patterns and returns a structured result. No external NLP dependencies are required.

## Setup

```python linenums="1"
from llmfy import PIIDetector, PIIMaskStyle, PIIStrategy, PIIType
```

## Strategies

### MASK + PARTIAL (default)

Replaces each PII value with its first two characters followed by `*` repeated for every remaining character.

```python linenums="1"
detector = PIIDetector()
result = detector.detect("Email: john@example.com, SSN: 123-45-6789")

print(result.processed_text)
# "Email: jo**************, SSN: 12*********"
```

### MASK + TYPE_NAME

Replaces each PII value with its type name in brackets.

```python linenums="1"
detector = PIIDetector(mask_style=PIIMaskStyle.TYPE_NAME)
result = detector.detect("Email: john@example.com, SSN: 123-45-6789")

print(result.processed_text)
# "Email: [EMAIL], SSN: [SSN]"
```

### REDACT

Replaces all PII with the generic `[REDACTED]` placeholder. `mask_style` is ignored.

```python linenums="1"
detector = PIIDetector(strategy=PIIStrategy.REDACT)
result = detector.detect("Email: john@example.com, SSN: 123-45-6789")

print(result.processed_text)
# "Email: [REDACTED], SSN: [REDACTED]"
```

## Filtering Types

Pass a `types` list to detect only specific PII categories. All other types are ignored.

```python linenums="1"
detector = PIIDetector(types=[PIIType.EMAIL, PIIType.PHONE_NUMBER])
result = detector.detect(
    "Reach me at alice@corp.com or (212) 555-0100. SSN: 111-22-3333 is untouched."
)

print(result.processed_text)
# "Reach me at al* or (2*. SSN: 111-22-3333 is untouched."
```

## Scanning Without Replacing

`scan()` returns all detections sorted by character position without modifying the text.

```python linenums="1"
detector = PIIDetector()
findings = detector.scan("admin@corp.com logged in from 10.0.0.1 on 2024-03-15")

for f in findings:
    print(f.pii_type, f.value, f.start, f.end)
# EMAIL     admin@corp.com  0  14
# IP_ADDRESS 10.0.0.1       30  38
# DATE_OF_BIRTH 2024-03-15  42  52
```

## Working with Results

`PIIDetectionResult` is a Pydantic model — call `model_dump()` to serialise it.

```python linenums="1"
result = detector.detect("Call me at 555-867-5309")

print(result.has_pii)          # True
print(result.strategy)         # mask
print(result.original_text)    # "Call me at 555-867-5309"
print(result.processed_text)   # "Call me at 55*********"

for d in result.detections:
    print(d.pii_type)          # PHONE_NUMBER
    print(d.value)             # 555-867-5309
    print(d.start, d.end)      # 11 23
    print(d.placeholder)       # 55*********
```

## Phone Number Formats

`PHONE_NUMBER` supports both compact international and US/`+1` formats.

```python linenums="1"
detector = PIIDetector(types=[PIIType.PHONE_NUMBER], mask_style=PIIMaskStyle.TYPE_NAME)

texts = [
    "+628987654321",    # compact international
    "+1 800 555-9876",  # +1 with spaces
    "(555) 123-4567",   # US with parens
    "555-123-4567",     # US dashes
]

for t in texts:
    r = detector.detect(t)
    print(r.processed_text)
# [PHONE_NUMBER]
# [PHONE_NUMBER]
# [PHONE_NUMBER]
# [PHONE_NUMBER]
```

## Constructor Reference

```python
PIIDetector(
    strategy: PIIStrategy = PIIStrategy.MASK,
    mask_style: PIIMaskStyle = PIIMaskStyle.PARTIAL,
    types: list[PIIType] | None = None,       # None = all types
    custom_types: dict[str, str | re.Pattern] | None = None,
)
```
