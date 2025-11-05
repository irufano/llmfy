from llmfy.llmfy_utils.text_processor import chunk_markdown_by_header

# Example Markdown
md_text = """
# Main Title

Intro paragraph for the document.

## Section 1
Details for section 1.

### Subsection 1.1
Information about subsection 1.1.

## Section 2
Content for section 2.

### Subsection 2.1
Nested content here.

#### Sub-subsection 2.1.1
Even more nested content.
"""

md_w_data = (
    """
# Main Title

Intro paragraph.

## Section 1
Details for section 1.

### Subsection 1.1
More info here.
""",
    {"source": "doc1.md", "author": "irufano"},
)

# --- Example Usage ---
print("🔹 All headers (default):")
chunks_all = chunk_markdown_by_header(md_text)
for c in chunks_all:
    print(f"\nLevel {c['level']} - {c['header']}")
    print(c["content"])
    print("-" * 60)

print("\n🔹 Only up to level 2:")
chunks_lvl2 = chunk_markdown_by_header(md_text, header_level=2)
for c in chunks_lvl2:
    print(f"\nLevel {c['level']} - {c['header']}")
    print(c["content"])
    print("-" * 60)


print("\n🔹 Meta data:")
chunks_lvl2 = chunk_markdown_by_header(md_w_data, header_level=2)
for c in chunks_lvl2:
    print(f"Level {c['level']} - {c['header']}")
    print(f"Metadata: {c.get('metadata')}")
    print(f"Content:\n{c['content']}")
    print("-" * 60)
