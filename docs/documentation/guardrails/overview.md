---
title: Overview
description: PII detection and masking guardrails for LLM input and output text.
---

# Guardrails

Guardrails protect your application by inspecting and sanitising text before it reaches an LLM or after it comes back. The first guardrail shipped in llmfy is **PII detection** — finding and replacing Personally Identifiable Information in any string.

## Key Concepts

| Concept | Description |
|---|---|
| **PIIType** | Enum of supported PII categories (EMAIL, SSN, CREDIT_CARD, …) |
| **PIIStrategy** | How to handle detected PII: `MASK` or `REDACT` |
| **PIIMaskStyle** | Placeholder format when strategy is `MASK`: `PARTIAL` or `TYPE_NAME` |
| **PIIDetector** | Main class — runs regex patterns, returns structured results |
| **PIIDetectionResult** | Pydantic model holding original text, processed text, and all detections |
| **PIIDetection** | A single PII finding with type, value, char positions, and placeholder |

## Supported PII Types

| PIIType | Example match |
|---|---|
| `EMAIL` | `john@example.com` |
| `PHONE_NUMBER` | `(555) 123-4567`, `+628987654321` |
| `SSN` | `123-45-6789` |
| `CREDIT_CARD` | `4111 1111 1111 1111` |
| `IP_ADDRESS` | `192.168.1.1` |
| `DATE_OF_BIRTH` | `01/15/1990`, `2024-03-15`, `January 1, 2000` |
| `PASSPORT_NUMBER` | `AB1234567` |

## Quick Start

```python linenums="1"
from llmfy import PIIDetector

detector = PIIDetector()
result = detector.detect("Contact john@example.com or call (555) 123-4567")

print(result.processed_text)  # "Contact jo************** or call (5************"
print(result.has_pii)         # True
print(len(result.detections)) # 2
```

## Detection Methods

| Method | Description |
|---|---|
| `detect(text)` | Returns `PIIDetectionResult` with PII replaced in `processed_text` |
| `scan(text)` | Returns `List[PIIDetection]` — finds PII without modifying the text |
