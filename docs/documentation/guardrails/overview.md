---
title: Overview
description: What Guardrails are in llmfy and which ones are available.
---

# Guardrails

Guardrails protect your application by inspecting and sanitizing text before it reaches an LLM or after it comes back — detecting sensitive content, replacing it with a safe placeholder, and (where supported) restoring it later.

Guardrails in llmfy are independent of the chat/generation API (`LLMfy`) and the workflow engine (`FlowEngine`) — they operate on plain strings, so you can use them anywhere in your pipeline: before building a prompt, after receiving a model response, or in any text-processing step in between.

## Available Guardrails

| Guardrail | Description |
|---|---|
| [PII Guard](pii-guard.md) | Detects and replaces Personally Identifiable Information (emails, phone numbers, national IDs, credit cards, etc.) using regex — no external NLP dependencies. Supports one-way masking (`PARTIAL`, `MASK`, `REDACT`) and reversible tokenization (`TOKENIZE` + `restore()`), plus custom, domain-specific PII patterns. |
