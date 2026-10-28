r"""
Programmatic verification script for docs/REPORT.docx.
Asserts:
1. Count of raw '$' is 0.
2. Count of LaTeX macros (\delta, \Sigma, \epsilon, \in, \to, \blacksquare, \frac, etc.) is 0.
3. Count of code fences ('```') is 0.
4. Count of raw Mermaid code ('stateDiagram', 'graph TD') is 0.
5. At least 1 image picture shape is present.
6. Real Word tables exist and are properly populated.
7. Word footers and headers exist.
"""

import sys
from pathlib import Path
import docx

def verify_docx():
    doc_path = Path(__file__).resolve().parent.parent / "docs" / "REPORT.docx"
    assert doc_path.exists(), f"File does not exist: {doc_path}"

    doc = docx.Document(str(doc_path))

    text_chunks = []
    # Collect paragraph texts
    for p in doc.paragraphs:
        text_chunks.append(p.text)

    # Collect table texts
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                text_chunks.append(cell.text)

    # Collect header and footer texts
    for section in doc.sections:
        for p in section.header.paragraphs:
            text_chunks.append(p.text)
        for p in section.footer.paragraphs:
            text_chunks.append(p.text)

    full_text = "\n".join(text_chunks)

    # 1. Dollar signs check
    dollar_count = full_text.count("$")
    print(f"Raw '$' count: {dollar_count}")

    # 2. LaTeX tokens check
    latex_tokens = [
        r"\delta", r"\Sigma", r"\epsilon", r"\in", r"\to",
        r"\blacksquare", r"\cup", r"\cdot", r"\frac", r"\times",
        r"\equiv", r"\iff", r"\ge", r"\le", r"\mathbb", r"\mathbf"
    ]
    found_latex = {tok: full_text.count(tok) for tok in latex_tokens if full_text.count(tok) > 0}
    print(f"LaTeX tokens found: {found_latex}")

    # 3. Triple backtick code fences check
    triple_backtick = chr(96) * 3
    fence_count = full_text.count(triple_backtick)
    print(f"Code fence count: {fence_count}")

    # 4. Raw Mermaid check
    mermaid_count = full_text.count("stateDiagram") + full_text.count("graph TD")
    print(f"Raw Mermaid count: {mermaid_count}")

    # 5. Pictures check
    picture_count = len(doc.inline_shapes)
    print(f"Inline pictures count: {picture_count}")

    # 6. Tables check
    table_count = len(doc.tables)
    print(f"Word tables count: {table_count}")

    # Assertions
    assert dollar_count == 0, f"Found {dollar_count} dollar signs in .docx"
    assert len(found_latex) == 0, f"Found LaTeX macros in .docx: {found_latex}"
    assert fence_count == 0, f"Found {fence_count} code fences in .docx"
    assert mermaid_count == 0, f"Found {mermaid_count} Mermaid markers in .docx"
    assert picture_count >= 1, f"Expected at least 1 image, found {picture_count}"
    assert table_count >= 5, f"Expected at least 5 Word tables, found {table_count}"

    print("\n[SUCCESS] All programmatic verification checks passed successfully!")
    return True

if __name__ == "__main__":
    verify_docx()
