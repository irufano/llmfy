"""
Google AI (Gemini) pricing per 1M tokens (USD).
Reference: https://ai.google.dev/pricing

--- Pricing Structures ---

Flat pricing:
```json
    "model-id": {
        "input": <float>,      # all input types same price
        "output": <float>,
    }
```

Per-type input pricing:
```json
    "model-id": {
        "input": {
            "default": <float>,    # fallback for unspecified types
            "text":    <float>,
            "image":   <float>,
            "video":   <float>,
            "audio":   <float>,
        },
        "output": <float>,
    }
```

Tiered pricing (flat input, threshold on total input tokens):
```json
    "model-id": {
        "input":        <float>,   # price when prompt <= threshold
        "input_high":   <float>,   # price when prompt > threshold
        "output":       <float>,
        "output_high":  <float>,
        "threshold":    <int>,
    }
```

Tiered + per-type pricing:
```json
    "model-id": {
        "input": {
            "default": <float>,
            "text":    <float>,
            "image":   <float>,
            "video":   <float>,
            "audio":   <float>,
        },
        "input_high": {            # high-tier prices (prompt > threshold)
            "default": <float>,
            "text":    <float>,
            "image":   <float>,
            "video":   <float>,
            "audio":   <float>,
        },
        "output":       <float>,
        "output_high":  <float>,
        "threshold":    <int>,
    }
```
"""

GOOGLEAI_PRICING = {
    # Gemini 2.0 family
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.0-flash-lite": {"input": 0.075, "output": 0.30},
    # Gemini 2.5 family
    "gemini-2.5-pro": {
        "input": 1.25,
        "output": 10.00,
        "input_high": 2.50,
        "output_high": 15.00,
        "threshold": 200000,
    },
    "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
    "gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40},
    "gemini-2.5-flash-lite-preview-09-2025": {"input": 0.10, "output": 0.40},
    # Gemini 3.0 family
    "gemini-3-flash-preview": {
        "input": {
            "default": 0.50,
            "text": 0.50,
            "image": 0.50,
            "video": 0.50,
            "audio": 1.00,
        },
        "output": 3.00,
    },
    # Gemini 3.1 family
    "gemini-3.1-flash-lite-preview": {
        "input": {
            "default": 0.25,
            "text": 0.25,
            "image": 0.25,
            "video": 0.25,
            "audio": 0.50,
        },
        "output": 1.50,
    },
    "gemini-3.1-pro-preview": {
        "input": 2.00,
        "output": 12.00,
        "input_high": 4.00,
        "output_high": 18.00,
        "threshold": 200000,
    },
    # Gemini Embedding
    "gemini-embedding-001": {"input": 0.15, "output": 0},
    "gemini-embedding-2-preview": {"input": 0.20, "output": 0}
}
