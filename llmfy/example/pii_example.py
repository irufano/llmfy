import re

from llmfy import PIIGuard, PIIStrategy, PIIType

text = (
    "Contact john.doe@example.com or call (555) 123-4567. "
    "Contact john.doe@example.com or call (555) 1234567. "
    "Contact john.doe@example.com or call 5551234567. "
    "SSN: 123-45-6789. Card: 4111 1111 1111 1111. "
    "IP: 192.168.1.1. DOB: 01/15/1990. "
    "Visit https://example.com. Passport: AB1234567."
    "Contact irufano@mail.com phone: +628987654321"
)

# PIIGuard() now defaults to detecting every PIIType, including the
# NER-backed PERSON_NAME/ADDRESS (requires the optional xx_ent_pii_sm spaCy
# model — see README). Blocks 1-22 below demonstrate the original
# regex-only types, so they explicitly exclude the NER types to keep this
# script runnable without that dependency; block 23 demonstrates the
# NER-backed types on their own.
NER_TYPES = [PIIType.PERSON_NAME, PIIType.ADDRESS]

# ─── 1. TOKENIZE (default) — reversible, numbered placeholder unique per value
print("=" * 60)
print("1. TOKENIZE (default) — reversible; see blocks 18-19 for restore() demos")
print("=" * 60)

guard = PIIGuard(exclude_types=NER_TYPES)  # strategy=TOKENIZE
result = guard.detect(text)

print(f"Original : {result.original_text}")
print(f"Processed: {result.processed_text}")
print(f"has_pii  : {result.has_pii}")
print(f"Strategy : {result.strategy}")
print(f"Detections ({len(result.detections)}):")
for d in result.detections:
    print(f"  [{d.pii_type}] '{d.value}' @ chars {d.start}-{d.end} → '{d.placeholder}'")

# ─── 2. MASK — numbered, type-specific placeholder ───────────────────────────
print("\n" + "=" * 60)
print("2. MASK — [EMAIL_1], [PHONE_NUMBER_1], ... (unique per value)")
print("=" * 60)

guard_mask = PIIGuard(strategy=PIIStrategy.MASK, exclude_types=NER_TYPES)
result2 = guard_mask.detect(text)

print(f"Original : {result2.original_text}")
print(f"Processed: {result2.processed_text}")
print(f"Detections ({len(result2.detections)}):")
for d in result2.detections:
    print(f"  [{d.pii_type}] '{d.value}' → '{d.placeholder}'")

# ─── 3. REDACT strategy — all PII replaced with [REDACTED] ───────────────────
print("\n" + "=" * 60)
print("3. REDACT strategy — all types, same generic placeholder")
print("=" * 60)

guard_redact = PIIGuard(strategy=PIIStrategy.REDACT, exclude_types=NER_TYPES)
result3 = guard_redact.detect(
    "Email: jane@test.org, Phone: +1 800 555-9876, SSN: 987-65-4321"
)
print(f"Original : {result3.original_text}")
print(f"Processed: {result3.processed_text}")
print(f"Detections: {len(result3.detections)}")

# ─── 4. Filtered types — PARTIAL ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("4. Filtered types — EMAIL and PHONE_NUMBER only (PARTIAL)")
print("=" * 60)

guard_filtered = PIIGuard(
    strategy=PIIStrategy.PARTIAL, types=[PIIType.EMAIL, PIIType.PHONE_NUMBER]
)
result4 = guard_filtered.detect(
    "Reach me at alice@corp.com or (212) 555-0100. SSN: 111-22-3333 is untouched."
)
print(f"Original : {result4.original_text}")
print(f"Processed: {result4.processed_text}")
print(f"Detections ({len(result4.detections)}): {[str(d.pii_type) for d in result4.detections]}")

# ─── 5. scan() — detect without replacing ────────────────────────────────────
print("\n" + "=" * 60)
print("5. scan() — find PII without modifying text")
print("=" * 60)

findings = guard.scan(
    "admin@corp.com logged in from 10.0.0.1 on 2024-03-15"
)
print(f"Findings ({len(findings)}):")
for f in findings:
    print(f"  [{f.pii_type}] '{f.value}' @ chars {f.start}-{f.end}")

# ─── 6. REDACT + filtered types ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("6. REDACT + filtered types — SSN only")
print("=" * 60)

guard_ssn_redact = PIIGuard(strategy=PIIStrategy.REDACT, types=[PIIType.SSN])
result6 = guard_ssn_redact.detect(
    "Name: Bob Smith, SSN: 000-11-2222, Email: bob@example.com"
)
print(f"Original : {result6.original_text}")
print(f"Processed: {result6.processed_text}")

# ─── 7. No PII in text ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("7. No PII — text is returned unchanged")
print("=" * 60)

result7 = guard.detect("Hello world, nothing sensitive here.")
print(f"Original : {result7.original_text}")
print(f"Processed: {result7.processed_text}")
print(f"has_pii  : {result7.has_pii}")

# ─── 8. Multiple PII of the same type — MASK numbering ───────────────────────
print("\n" + "=" * 60)
print("8. Multiple PII of the same type — MASK gives each value its own number")
print("=" * 60)

result8 = guard_mask.detect(
    "Primary: alice@example.com, Secondary: bob@example.com, "
    "CC: carol@example.com, Repeat: alice@example.com"
)
print(f"Processed: {result8.processed_text}")
print(f"EMAIL detections: {len([d for d in result8.detections if d.pii_type == PIIType.EMAIL])}")
print("Note: 'alice@example.com' repeats but reuses the same [EMAIL_1] placeholder")

# ─── 9. PIIDetectionResult model fields ──────────────────────────────────────
print("\n" + "=" * 60)
print("9. PIIDetectionResult model serialization")
print("=" * 60)

result9 = guard.detect("Call me at 555-867-5309")
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

# ─── 11. Custom types — str pattern + PARTIAL ────────────────────────────────
print("\n" + "=" * 60)
print("11. Custom types — str pattern (PARTIAL)")
print("=" * 60)

guard_custom = PIIGuard(
    strategy=PIIStrategy.PARTIAL,
    exclude_types=NER_TYPES,
    custom_types={
        "EMPLOYEE_ID": r"EMP-\d{6}",
        "PROJECT_CODE": r"PRJ-[A-Z]{3}",
    },
)
result11 = guard_custom.detect(
    "Employee EMP-001234 is on project PRJ-ABC and emailed john@corp.com"
)
print(f"Original : {result11.original_text}")
print(f"Processed: {result11.processed_text}")
print(f"Detections ({len(result11.detections)}):")
for d in result11.detections:
    print(f"  [{d.pii_type}] '{d.value}' → '{d.placeholder}'")

# ─── 12. Custom types — MASK strategy ────────────────────────────────────────
print("\n" + "=" * 60)
print("12. Custom types — MASK strategy")
print("=" * 60)

guard_custom_mask = PIIGuard(
    strategy=PIIStrategy.MASK,
    exclude_types=NER_TYPES,
    custom_types={
        "EMPLOYEE_ID": r"EMP-\d{6}",
        "PROJECT_CODE": r"PRJ-[A-Z]{3}",
    },
)
result12 = guard_custom_mask.detect(
    "Employee EMP-001234 is on project PRJ-ABC and emailed john@corp.com"
)
print(f"Original : {result12.original_text}")
print(f"Processed: {result12.processed_text}")

# ─── 13. Custom types — compiled re.Pattern ──────────────────────────────────
print("\n" + "=" * 60)
print("13. Custom types — compiled re.Pattern")
print("=" * 60)

guard_compiled = PIIGuard(
    exclude_types=NER_TYPES,
    custom_types={
        "API_TOKEN": re.compile(r"tok_[a-z0-9]+"),
        "ORDER_ID": re.compile(r"ORD-\d{8}"),
    },
)
result13 = guard_compiled.detect(
    "Token tok_abc123xyz for order ORD-20240315"
)
print(f"Original : {result13.original_text}")
print(f"Processed: {result13.processed_text}")

# ─── 14. Custom types + REDACT ───────────────────────────────────────────────
print("\n" + "=" * 60)
print("14. Custom types + REDACT")
print("=" * 60)

guard_custom_redact = PIIGuard(
    strategy=PIIStrategy.REDACT,
    types=[],
    custom_types={"EMPLOYEE_ID": r"EMP-\d{6}"},
)
result14 = guard_custom_redact.detect(
    "ID: EMP-001234, Email: bob@example.com (email untouched — types=[])"
)
print(f"Original : {result14.original_text}")
print(f"Processed: {result14.processed_text}")

# ─── 15. Custom types combined with built-in types ───────────────────────────
print("\n" + "=" * 60)
print("15. Custom types combined with built-in types")
print("=" * 60)

guard_combined = PIIGuard(
    types=[PIIType.EMAIL, PIIType.PHONE_NUMBER],
    custom_types={"EMPLOYEE_ID": r"EMP-\d{6}"},
)
result15 = guard_combined.detect(
    "Staff EMP-007890 reached at carol@example.com or +628987654321"
)
print(f"Original : {result15.original_text}")
print(f"Processed: {result15.processed_text}")
print(f"Detections ({len(result15.detections)}): {[str(d.pii_type) for d in result15.detections]}")

# ─── 16. Custom type overrides built-in (same name) ──────────────────────────
print("\n" + "=" * 60)
print("16. Custom type overrides built-in — same name")
print("=" * 60)

guard_override = PIIGuard(
    exclude_types=NER_TYPES,
    custom_types={"EMAIL": r"custom-\w+@\w+\.com"},
)
result16 = guard_override.detect(
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

guard_partial_override = PIIGuard(
    exclude_types=NER_TYPES,
    custom_types={"PHONE_NUMBER": r"\+62\d{9,12}"},
)
result17 = guard_partial_override.detect(
    "Call +628987654321 or (555) 123-4567, email bob@test.com"
)
print(f"Original : {result17.original_text}")
print(f"Processed: {result17.processed_text}")
print(f"Detections ({len(result17.detections)}):")
for d in result17.detections:
    print(f"  [{d.pii_type}] '{d.value}' → '{d.placeholder}'")
print("Note: (555) 123-4567 untouched — custom PHONE_NUMBER only matches +62 format")

# ─── 18. TOKENIZE — reversible masking via detect() + restore() ──────────────
print("\n" + "=" * 60)
print("18. TOKENIZE — detect() then restore() using the returned detections")
print("=" * 60)

guard_tokenize = PIIGuard(strategy=PIIStrategy.TOKENIZE, exclude_types=NER_TYPES)
result18 = guard_tokenize.detect(
    "Contact john.doe@example.com or backup alice@example.com"
)
print(f"Original : {result18.original_text}")
print(f"Processed: {result18.processed_text}")

# The caller holds on to result18.detections themselves — PIIGuard stores nothing.
restored = guard_tokenize.restore(result18.processed_text, result18.detections)
print(f"Restored : {restored}")
print(f"Matches original: {restored == result18.original_text}")

# ─── 19. TOKENIZE — restoring placeholders inside different, later text ──────
print("\n" + "=" * 60)
print("19. TOKENIZE — restoring tokens embedded in new text (e.g. an LLM reply)")
print("=" * 60)

result19 = guard_tokenize.detect("My email is john.doe@example.com")
print(f"Processed         : {result19.processed_text}")

# Simulate a downstream system (e.g. an LLM) echoing the token back inside new text.
llm_reply = f"Sure, I'll send the confirmation to {result19.detections[0].placeholder} shortly."
print(f"Downstream text   : {llm_reply}")

restored_reply = guard_tokenize.restore(llm_reply, result19.detections)
print(f"Restored          : {restored_reply}")

# ─── 20. NIK — plain 16-digit Indonesian ID number ───────────────────────────
print("\n" + "=" * 60)
print("20. NIK — plain 16-digit Indonesian ID number")
print("=" * 60)

guard_id = PIIGuard(strategy=PIIStrategy.MASK, exclude_types=NER_TYPES)
result20 = guard_id.detect(
    "NIK saya 3171012501990001, No KK 3171012501990002"
)
print(f"Original : {result20.original_text}")
print(f"Processed: {result20.processed_text}")
print(f"Detections ({len(result20.detections)}):")
for d in result20.detections:
    print(f"  [{d.pii_type}] '{d.value}' → '{d.placeholder}'")
print(
    "Note: there's no separate KK_NUMBER type — Kartu Keluarga numbers use "
    "the same plain 16-digit format as NIK with no structural way to tell "
    "them apart by regex alone, so both are detected as NIK."
)

# ─── 21. PASSPORT_NUMBER — covers the Indonesian format too ──────────────────
print("\n" + "=" * 60)
print("21. PASSPORT_NUMBER — covers Indonesian (1 letter + 7 digits) and other formats")
print("=" * 60)

result21 = guard_id.detect(
    "Paspor: C1234567, Old format: AB12345678"
)
print(f"Original : {result21.original_text}")
print(f"Processed: {result21.processed_text}")
print(f"Detections ({len(result21.detections)}):")
for d in result21.detections:
    print(f"  [{d.pii_type}] '{d.value}' → '{d.placeholder}'")

# ─── 22. exclude_types — detect all built-in types except the ones listed ────
print("\n" + "=" * 60)
print("22. exclude_types — detect everything except SSN")
print("=" * 60)

guard_excluded = PIIGuard(
    strategy=PIIStrategy.MASK, exclude_types=[PIIType.SSN, *NER_TYPES]
)
result22 = guard_excluded.detect(
    "Email: jane@test.org, SSN: 123-45-6789"
)
print(f"Original : {result22.original_text}")
print(f"Processed: {result22.processed_text}")
print(f"Detections ({len(result22.detections)}): {[str(d.pii_type) for d in result22.detections]}")
print("Note: SSN is skipped; every other built-in type still runs")

try:
    PIIGuard(types=[PIIType.EMAIL], exclude_types=[PIIType.SSN])
except ValueError as e:
    print(f"types + exclude_types together raises: {e}")

# ─── 23. PERSON_NAME / ADDRESS — spaCy NER (requires xx_ent_pii_sm) ──────────
print("\n" + "=" * 60)
print("23. PERSON_NAME / ADDRESS — spaCy NER-backed detection")
print("=" * 60)

try:
    guard_ner = PIIGuard(types=NER_TYPES, strategy=PIIStrategy.MASK)
    result23 = guard_ner.detect(
        "Budi Santoso dan Irfan tinggal di Jl. Merdeka No. 10, Jakarta."
    )
    print(f"Original : {result23.original_text}")
    print(f"Processed: {result23.processed_text}")
    print(f"Detections ({len(result23.detections)}):")
    for d in result23.detections:
        print(f"  [{d.pii_type}] '{d.value}' → '{d.placeholder}'")
except Exception as e:
    print(f"Skipped — xx_ent_pii_sm not installed: {e}")

# ─── 24. Opt out of the NER-backed types entirely ────────────────────────────
print("\n" + "=" * 60)
print("24. exclude_types — stay regex-only, no spaCy dependency required")
print("=" * 60)

guard_regex_only = PIIGuard(exclude_types=NER_TYPES)
result24 = guard_regex_only.detect(
    "Contact john.doe@example.com — Budi Santoso, Jl. Merdeka No. 10, Jakarta."
)
print(f"Original : {result24.original_text}")
print(f"Processed: {result24.processed_text}")
print(
    "Note: PIIGuard() now defaults to detecting every PIIType, including the "
    "NER-backed PERSON_NAME/ADDRESS — pass exclude_types=[PIIType.PERSON_NAME, "
    "PIIType.ADDRESS] (as above) to keep the old regex-only, zero-dependency behavior."
)
