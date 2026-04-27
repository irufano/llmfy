# PII Detector Example

```python linenums="1"
import re

from llmfy import PIIDetector, PIIMaskStyle, PIIStrategy, PIIType

text = (
    "Contact john.doe@example.com or call (555) 123-4567. "
    "Contact john.doe@example.com or call (555) 1234567. "
    "Contact john.doe@example.com or call 5551234567. "
    "SSN: 123-45-6789. Card: 4111 1111 1111 1111. "
    "IP: 192.168.1.1. DOB: 01/15/1990. "
    "Visit https://example.com. Passport: AB1234567."
    "Contact irufano@mail.com phone: +628987654321"
)

# ─── 1. MASK + PARTIAL (default) ─────────────────────────────────────────────
print("=" * 60)
print("1. MASK + PARTIAL (default) — first 2 chars of value + *")
print("=" * 60)

detector = PIIDetector()  # strategy=MASK, mask_style=PARTIAL
result = detector.detect(text)

print(f"Original : {result.original_text}")
print(f"Processed: {result.processed_text}")
print(f"has_pii  : {result.has_pii}")
print(f"Strategy : {result.strategy}")
print(f"Detections ({len(result.detections)}):")
for d in result.detections:
    print(f"  [{d.pii_type}] '{d.value}' @ chars {d.start}-{d.end} → '{d.placeholder}'")

# ─── 2. MASK + TYPE_NAME ──────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("2. MASK + TYPE_NAME — [EMAIL], [PHONE_NUMBER], ...")
print("=" * 60)

detector_type_name = PIIDetector(mask_style=PIIMaskStyle.TYPE_NAME)
result2 = detector_type_name.detect(text)

print(f"Original : {result2.original_text}")
print(f"Processed: {result2.processed_text}")
print(f"Detections ({len(result2.detections)}):")
for d in result2.detections:
    print(f"  [{d.pii_type}] '{d.value}' → '{d.placeholder}'")

# ─── 3. REDACT strategy — all PII replaced with [REDACTED] ───────────────────
print("\n" + "=" * 60)
print("3. REDACT strategy — all types (mask_style ignored)")
print("=" * 60)

detector_redact = PIIDetector(strategy=PIIStrategy.REDACT)
result3 = detector_redact.detect(
    "Email: jane@test.org, Phone: +1 800 555-9876, SSN: 987-65-4321"
)
print(f"Original : {result3.original_text}")
print(f"Processed: {result3.processed_text}")
print(f"Detections: {len(result3.detections)}")

# ─── 4. Filtered types — PARTIAL ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("4. Filtered types — EMAIL and PHONE_NUMBER only (PARTIAL)")
print("=" * 60)

detector_filtered = PIIDetector(types=[PIIType.EMAIL, PIIType.PHONE_NUMBER])
result4 = detector_filtered.detect(
    "Reach me at alice@corp.com or (212) 555-0100. SSN: 111-22-3333 is untouched."
)
print(f"Original : {result4.original_text}")
print(f"Processed: {result4.processed_text}")
print(f"Detections ({len(result4.detections)}): {[str(d.pii_type) for d in result4.detections]}")

# ─── 5. scan() — detect without replacing ────────────────────────────────────
print("\n" + "=" * 60)
print("5. scan() — find PII without modifying text")
print("=" * 60)

findings = detector.scan(
    "admin@corp.com logged in from 10.0.0.1 on 2024-03-15"
)
print(f"Findings ({len(findings)}):")
for f in findings:
    print(f"  [{f.pii_type}] '{f.value}' @ chars {f.start}-{f.end}")

# ─── 6. REDACT + filtered types ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("6. REDACT + filtered types — SSN only")
print("=" * 60)

detector_ssn_redact = PIIDetector(strategy=PIIStrategy.REDACT, types=[PIIType.SSN])
result6 = detector_ssn_redact.detect(
    "Name: Bob Smith, SSN: 000-11-2222, Email: bob@example.com"
)
print(f"Original : {result6.original_text}")
print(f"Processed: {result6.processed_text}")

# ─── 7. No PII in text ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("7. No PII — text is returned unchanged")
print("=" * 60)

result7 = detector.detect("Hello world, nothing sensitive here.")
print(f"Original : {result7.original_text}")
print(f"Processed: {result7.processed_text}")
print(f"has_pii  : {result7.has_pii}")

# ─── 8. Multiple PII of the same type ────────────────────────────────────────
print("\n" + "=" * 60)
print("8. Multiple PII of the same type")
print("=" * 60)

result8 = detector.detect(
    "Primary: alice@example.com, Secondary: bob@example.com, CC: carol@example.com"
)
print(f"Processed: {result8.processed_text}")
print(f"EMAIL detections: {len([d for d in result8.detections if d.pii_type == PIIType.EMAIL])}")

# ─── 9. PIIDetectionResult model fields ──────────────────────────────────────
print("\n" + "=" * 60)
print("9. PIIDetectionResult model serialization")
print("=" * 60)

result9 = detector.detect("Call me at 555-867-5309")
print(f"Result ID       : {result9.id}")
print(f"has_pii         : {result9.has_pii}")
print(f"model_dump keys : {list(result9.model_dump().keys())}")

# ─── 10. Enum values ─────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("10. Enum values")
print("=" * 60)

print("PIIType values:")
for t in PIIType:
    print(f"  {t!r} → str: '{t}'")

print("PIIStrategy values:")
for s in PIIStrategy:
    print(f"  {s!r} → str: '{s}'")

print("PIIMaskStyle values:")
for m in PIIMaskStyle:
    print(f"  {m!r} → str: '{m}'")

# ─── 11. Custom types — str pattern + PARTIAL ────────────────────────────────
print("\n" + "=" * 60)
print("11. Custom types — str pattern (PARTIAL default)")
print("=" * 60)

detector_custom = PIIDetector(
    custom_types={
        "EMPLOYEE_ID": r"EMP-\d{6}",
        "PROJECT_CODE": r"PRJ-[A-Z]{3}",
    }
)
result11 = detector_custom.detect(
    "Employee EMP-001234 is on project PRJ-ABC and emailed john@corp.com"
)
print(f"Original : {result11.original_text}")
print(f"Processed: {result11.processed_text}")
print(f"Detections ({len(result11.detections)}):")
for d in result11.detections:
    print(f"  [{d.pii_type}] '{d.value}' → '{d.placeholder}'")

# ─── 12. Custom types — TYPE_NAME style ──────────────────────────────────────
print("\n" + "=" * 60)
print("12. Custom types — TYPE_NAME style")
print("=" * 60)

detector_custom_tn = PIIDetector(
    mask_style=PIIMaskStyle.TYPE_NAME,
    custom_types={
        "EMPLOYEE_ID": r"EMP-\d{6}",
        "PROJECT_CODE": r"PRJ-[A-Z]{3}",
    }
)
result12 = detector_custom_tn.detect(
    "Employee EMP-001234 is on project PRJ-ABC and emailed john@corp.com"
)
print(f"Original : {result12.original_text}")
print(f"Processed: {result12.processed_text}")

# ─── 13. Custom types — compiled re.Pattern ──────────────────────────────────
print("\n" + "=" * 60)
print("13. Custom types — compiled re.Pattern")
print("=" * 60)

detector_compiled = PIIDetector(
    custom_types={
        "API_TOKEN": re.compile(r"tok_[a-z0-9]+"),
        "ORDER_ID": re.compile(r"ORD-\d{8}"),
    }
)
result13 = detector_compiled.detect(
    "Token tok_abc123xyz for order ORD-20240315"
)
print(f"Original : {result13.original_text}")
print(f"Processed: {result13.processed_text}")

# ─── 14. Custom types + REDACT ───────────────────────────────────────────────
print("\n" + "=" * 60)
print("14. Custom types + REDACT (mask_style ignored)")
print("=" * 60)

detector_custom_redact = PIIDetector(
    strategy=PIIStrategy.REDACT,
    types=[],
    custom_types={"EMPLOYEE_ID": r"EMP-\d{6}"},
)
result14 = detector_custom_redact.detect(
    "ID: EMP-001234, Email: bob@example.com (email untouched — types=[])"
)
print(f"Original : {result14.original_text}")
print(f"Processed: {result14.processed_text}")

# ─── 15. Custom types combined with built-in types ───────────────────────────
print("\n" + "=" * 60)
print("15. Custom types combined with built-in types")
print("=" * 60)

detector_combined = PIIDetector(
    types=[PIIType.EMAIL, PIIType.PHONE_NUMBER],
    custom_types={"EMPLOYEE_ID": r"EMP-\d{6}"},
)
result15 = detector_combined.detect(
    "Staff EMP-007890 reached at carol@example.com or +628987654321"
)
print(f"Original : {result15.original_text}")
print(f"Processed: {result15.processed_text}")
print(f"Detections ({len(result15.detections)}): {[str(d.pii_type) for d in result15.detections]}")

# ─── 16. Custom type overrides built-in (same name) ──────────────────────────
print("\n" + "=" * 60)
print("16. Custom type overrides built-in — same name")
print("=" * 60)

detector_override = PIIDetector(
    custom_types={"EMAIL": r"custom-\w+@\w+\.com"}
)
result16 = detector_override.detect(
    "Regular john@example.com and custom-user@corp.com"
)
print(f"Original : {result16.original_text}")
print(f"Processed: {result16.processed_text}")
print(f"Detections ({len(result16.detections)}):")
for d in result16.detections:
    print(f"  [{d.pii_type}] '{d.value}' → '{d.placeholder}'")
print("Note: john@example.com untouched — built-in EMAIL replaced by custom pattern")

# ─── 17. Partial override — one built-in replaced, others intact ─────────────
print("\n" + "=" * 60)
print("17. Partial override — PHONE_NUMBER replaced, EMAIL intact")
print("=" * 60)

detector_partial_override = PIIDetector(
    custom_types={"PHONE_NUMBER": r"\+62\d{9,12}"}
)
result17 = detector_partial_override.detect(
    "Call +628987654321 or (555) 123-4567, email bob@test.com"
)
print(f"Original : {result17.original_text}")
print(f"Processed: {result17.processed_text}")
print(f"Detections ({len(result17.detections)}):")
for d in result17.detections:
    print(f"  [{d.pii_type}] '{d.value}' → '{d.placeholder}'")
print("Note: (555) 123-4567 untouched — custom PHONE_NUMBER only matches +62 format")
```