---
title: Custom PII Types
description: Define your own PII patterns alongside or instead of built-in types.
---

# Custom PII Types

`PIIDetector` accepts a `custom_types` dict so you can define domain-specific PII patterns — employee IDs, internal codes, API tokens, or any regex you need.

## Setup

```python linenums="1"
from llmfy import PIIDetector, PIIMaskStyle, PIIStrategy
```

## Adding Custom Types

Pass a dict mapping a **type name** (str) to a **regex pattern** (str or compiled `re.Pattern`). The type name becomes the placeholder label when `mask_style=TYPE_NAME`, and the first two characters are used for `PARTIAL`.

### String Pattern

```python linenums="1"
detector = PIIDetector(
    custom_types={
        "EMPLOYEE_ID": r"EMP-\d{6}",
        "PROJECT_CODE": r"PRJ-[A-Z]{3}",
    }
)
result = detector.detect(
    "Employee EMP-001234 is on project PRJ-ABC and emailed john@corp.com"
)

print(result.processed_text)
# "Employee EM* is on project PR* and emailed jo*"
```

### Compiled Pattern

```python linenums="1"
import re

detector = PIIDetector(
    custom_types={
        "API_TOKEN": re.compile(r"tok_[a-z0-9]+"),
        "ORDER_ID": re.compile(r"ORD-\d{8}"),
    }
)
result = detector.detect("Token tok_abc123xyz for order ORD-20240315")

print(result.processed_text)
# "Token to* for order OR*"
```

## Custom Types with TYPE_NAME Style

```python linenums="1"
detector = PIIDetector(
    mask_style=PIIMaskStyle.TYPE_NAME,
    custom_types={
        "EMPLOYEE_ID": r"EMP-\d{6}",
        "PROJECT_CODE": r"PRJ-[A-Z]{3}",
    }
)
result = detector.detect(
    "Employee EMP-001234 is on project PRJ-ABC and emailed john@corp.com"
)

print(result.processed_text)
# "Employee [EMPLOYEE_ID] is on project [PROJECT_CODE] and emailed [EMAIL]"
```

## Custom Types with REDACT

`mask_style` is ignored when `strategy=REDACT`.

```python linenums="1"
detector = PIIDetector(
    strategy=PIIStrategy.REDACT,
    types=[],
    custom_types={"EMPLOYEE_ID": r"EMP-\d{6}"},
)
result = detector.detect(
    "ID: EMP-001234, Email: bob@example.com"
)

print(result.processed_text)
# "ID: [REDACTED], Email: bob@example.com"
```

!!! note
    `types=[]` disables all built-in PII types. Only the custom patterns run.

## Combining Custom and Built-in Types

Custom types run alongside the built-in `types` list.

```python linenums="1"
from llmfy import PIIDetector, PIIType

detector = PIIDetector(
    types=[PIIType.EMAIL, PIIType.PHONE_NUMBER],
    custom_types={"EMPLOYEE_ID": r"EMP-\d{6}"},
)
result = detector.detect(
    "Staff EMP-007890 reached at carol@example.com or +628987654321"
)

print(result.processed_text)
# "Staff EM* reached at ca* or +6*"

print([str(d.pii_type) for d in result.detections])
# ['EMPLOYEE_ID', 'EMAIL', 'PHONE_NUMBER']
```

## Overriding a Built-in Type

If a custom type name matches a built-in `PIIType` value (e.g. `"EMAIL"`), the custom pattern **replaces** the built-in one entirely. The built-in pattern is suppressed.

```python linenums="1"
# Only matches custom-*@*.com — standard email addresses are left alone
detector = PIIDetector(
    custom_types={"EMAIL": r"custom-\w+@\w+\.com"}
)
result = detector.detect(
    "Regular john@example.com and custom-user@corp.com"
)

print(result.processed_text)
# "Regular john@example.com and cu*"
```

### Partial Override

Override one built-in type while leaving the rest active.

```python linenums="1"
# PHONE_NUMBER now only matches +62 (Indonesian) numbers
detector = PIIDetector(
    custom_types={"PHONE_NUMBER": r"\+62\d{9,12}"}
)
result = detector.detect(
    "Call +628987654321 or (555) 123-4567, email bob@test.com"
)

print(result.processed_text)
# "Call +6* or (555) 123-4567, email bo*"
```

`(555) 123-4567` is left untouched because the built-in `PHONE_NUMBER` pattern is suppressed, and the custom pattern does not match it. `EMAIL` continues to work normally since it was not overridden.
