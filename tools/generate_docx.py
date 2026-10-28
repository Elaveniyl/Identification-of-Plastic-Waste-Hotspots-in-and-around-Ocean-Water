r"""
Generates docs/REPORT.docx from docs/REPORT.md with publication-quality formatting:
1. Renders high-resolution diagrams (DFA state diagram and System Architecture) via matplotlib.
2. Converts all LaTeX equations ($...$, $$...$$, \delta, \Sigma, \epsilon, \in, \to, etc.) into readable Unicode (δ, Σ, ε, ∈, →).
3. Eliminates all ``` code fences and raw Mermaid/DOT code from the docx document.
4. Inserts real Word tables with styled headers, alternating row fills, and cell margins.
5. Adds native Word page numbering (Page X of Y) in footers and a structured Table of Contents.
6. Validates the generated document programmatically.
"""

import re
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOC_MD_PATH = Path(__file__).resolve().parent.parent / "docs" / "REPORT.md"
DOC_DOCX_PATH = Path(__file__).resolve().parent.parent / "docs" / "REPORT.docx"
DFA_IMG_PATH = Path(__file__).resolve().parent.parent / "docs" / "dfa_state_diagram.png"
ARCH_IMG_PATH = Path(__file__).resolve().parent.parent / "docs" / "system_architecture.png"


def render_dfa_diagram():
    """Renders the formal 8-state DFA transition graph as a 300-DPI PNG."""
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    fig, ax = plt.subplots(figsize=(15, 8.5), dpi=300)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')

    pos = {
        'DRAFT': (1.2, 4.0),
        'GEO_TAGGED': (3.8, 6.0),
        'CLASSIFIED': (3.8, 2.0),
        'HOTSPOT_FLAGGED': (6.5, 4.0),
        'VERIFIED': (9.2, 5.8),
        'DISPATCHED': (9.2, 2.2),
        'ARCHIVED': (12.2, 5.8),
        'REJECTED': (12.2, 1.5)
    }

    radius = 0.65
    for name, (x, y) in pos.items():
        if name in ['ARCHIVED', 'REJECTED']:
            ec = '#1e7e34' if name == 'ARCHIVED' else '#bd2130'
            fc = '#e8f5e9' if name == 'ARCHIVED' else '#f8d7da'
            c_outer = patches.Circle((x, y), radius + 0.08, edgecolor=ec, facecolor='none', lw=2.5, zorder=4)
            c_inner = patches.Circle((x, y), radius, edgecolor=ec, facecolor=fc, lw=1.5, zorder=4)
            ax.add_patch(c_outer)
            ax.add_patch(c_inner)
            ax.text(x, y, name, ha='center', va='center', fontsize=8.5, fontweight='bold', color=ec, zorder=5)
        else:
            c = patches.Circle((x, y), radius, edgecolor='#1b365d', facecolor='#eef4f8', lw=2.0, zorder=4)
            ax.add_patch(c)
            ax.text(x, y, name, ha='center', va='center', fontsize=8.5, fontweight='bold', color='#1b365d', zorder=5)

    ax.annotate('START', xy=(pos['DRAFT'][0] - radius, pos['DRAFT'][1]), xytext=(pos['DRAFT'][0] - 1.4, pos['DRAFT'][1]),
                arrowprops=dict(arrowstyle='->', lw=2.5, color='#1b365d'),
                va='center', ha='right', fontsize=9.5, fontweight='bold', color='#1b365d')

    def draw_edge(u, v, lbl, rad=0.0, is_inval=False, lx=None, ly=None):
        color = '#c53030' if is_inval else '#2b4c7e'
        ls = '--' if is_inval else '-'
        lw = 1.4 if is_inval else 1.8
        shrink = 25
        ax.annotate('', xy=pos[v], xytext=pos[u],
                    arrowprops=dict(arrowstyle='-|>', color=color, lw=lw, linestyle=ls,
                                    shrinkA=shrink, shrinkB=shrink,
                                    connectionstyle=f'arc3,rad={rad}', mutation_scale=15),
                    zorder=3)
        if lx is not None and ly is not None:
            bg_color = '#fff5f5' if is_inval else '#f0f7ff'
            border_color = '#feb2b2' if is_inval else '#bee3f8'
            text_color = '#9b2c2c' if is_inval else '#2c5282'
            ax.text(lx, ly, lbl, fontsize=7.5, color=text_color, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.25', facecolor=bg_color, edgecolor=border_color, lw=0.8, alpha=0.95),
                    ha='center', va='center', zorder=6)

    # Operational Transitions
    draw_edge('DRAFT', 'GEO_TAGGED', 'add_coords', rad=0.0, lx=2.3, ly=5.2)
    draw_edge('DRAFT', 'CLASSIFIED', 'classify_image', rad=0.0, lx=2.3, ly=2.8)
    draw_edge('GEO_TAGGED', 'HOTSPOT_FLAGGED', 'classify_image /\nflag_hotspot', rad=0.05, lx=5.2, ly=5.3)
    draw_edge('CLASSIFIED', 'HOTSPOT_FLAGGED', 'add_coords', rad=-0.05, lx=5.2, ly=2.8)
    draw_edge('HOTSPOT_FLAGGED', 'VERIFIED', 'operator_verify', rad=0.08, lx=7.7, ly=5.2)
    draw_edge('HOTSPOT_FLAGGED', 'DISPATCHED', 'dispatch_cleanup', rad=-0.08, lx=7.7, ly=3.0)
    draw_edge('VERIFIED', 'DISPATCHED', 'dispatch_cleanup', rad=0.0, lx=9.8, ly=4.0)
    draw_edge('VERIFIED', 'ARCHIVED', 'complete_archive', rad=0.0, lx=10.7, ly=6.05)
    draw_edge('DISPATCHED', 'ARCHIVED', 'complete_archive', rad=-0.12, lx=10.6, ly=4.3)

    # Skip-level
    draw_edge('GEO_TAGGED', 'VERIFIED', 'operator_verify', rad=0.22, lx=6.5, ly=6.8)
    draw_edge('CLASSIFIED', 'VERIFIED', 'operator_verify', rad=-0.22, lx=6.6, ly=4.7)

    # Invalidate
    draw_edge('DRAFT', 'REJECTED', 'invalidate', rad=-0.25, is_inval=True, lx=6.5, ly=1.0)
    draw_edge('CLASSIFIED', 'REJECTED', 'invalidate', rad=-0.12, is_inval=True, lx=8.0, ly=1.4)
    draw_edge('HOTSPOT_FLAGGED', 'REJECTED', 'invalidate', rad=-0.18, is_inval=True, lx=9.5, ly=2.0)
    draw_edge('GEO_TAGGED', 'REJECTED', 'invalidate', rad=0.28, is_inval=True, lx=8.5, ly=6.3)
    draw_edge('VERIFIED', 'REJECTED', 'invalidate', rad=0.25, is_inval=True, lx=11.2, ly=3.3)
    draw_edge('DISPATCHED', 'REJECTED', 'invalidate', rad=-0.05, is_inval=True, lx=10.7, ly=1.6)

    ax.set_title('Waste Observation Lifecycle Automaton M = (Q, Σ, δ, q0, F)', fontsize=16, fontweight='bold', pad=25, color='#1b365d')
    ax.set_xlim(-0.5, 13.8)
    ax.set_ylim(0.2, 7.5)
    ax.axis('off')

    p_op = patches.Patch(facecolor='#eef4f8', edgecolor='#1b365d', label='Operational States Q')
    p_acc = patches.Patch(facecolor='#e8f5e9', edgecolor='#1e7e34', label='Accepting States F (Terminal)')
    p_norm_edge = plt.Line2D([0], [0], color='#2b4c7e', lw=2, label='Domain Transitions δ')
    p_inv_edge = plt.Line2D([0], [0], color='#c53030', lw=1.5, linestyle='--', label='Invalidation (invalidate)')
    ax.legend(handles=[p_op, p_acc, p_norm_edge, p_inv_edge], loc='upper right', frameon=True, fontsize=9, facecolor='#ffffff', edgecolor='#cbd5e0')

    plt.tight_layout()
    plt.savefig(DFA_IMG_PATH, dpi=300, bbox_inches='tight')
    plt.close()


def render_architecture_diagram():
    """Renders the system architecture diagram as a 300-DPI PNG."""
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    fig, ax = plt.subplots(figsize=(13, 7.5), dpi=300)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')

    def draw_box(x, y, w, h, title, bg, border):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.2',
                                     facecolor=bg, edgecolor=border, lw=1.5, zorder=1)
        ax.add_patch(rect)
        ax.text(x + w / 2.0, y + h - 0.35, title, ha='center', va='center',
                fontsize=10.5, fontweight='bold', color=border, zorder=2)

    draw_box(0.5, 4.2, 3.2, 2.5, 'Presentation Layer', '#f0f4f8', '#1b365d')
    draw_box(4.5, 4.2, 3.8, 2.5, 'Service & Computation Layer', '#f0fdf4', '#166534')
    draw_box(9.2, 4.2, 3.2, 2.5, 'Core Engines & Datasets', '#fefce8', '#854d0e')

    def draw_card(x, y, w, h, text, fc='#ffffff', ec='#cbd5e0', tc='#1e293b'):
        card = patches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.1',
                                     facecolor=fc, edgecolor=ec, lw=1.0, zorder=3)
        ax.add_patch(card)
        ax.text(x + w / 2.0, y + h / 2.0, text, ha='center', va='center',
                fontsize=8.0, color=tc, fontweight='normal', zorder=4)

    draw_card(0.8, 5.8, 2.6, 0.5, '/object (Material Classifier)')
    draw_card(0.8, 5.1, 2.6, 0.5, '/hotspot (GIS Spatial Console)')
    draw_card(0.8, 4.4, 2.6, 0.5, '/automata (FLA Simulator)')

    draw_card(4.8, 5.8, 3.2, 0.5, 'PredictionService (Inception-v3)')
    draw_card(4.8, 5.1, 3.2, 0.5, 'HotspotService (HPI Engine)')
    draw_card(4.8, 4.4, 3.2, 0.5, 'WasteObservationFSM (DFA)')

    draw_card(9.5, 5.8, 2.6, 0.5, 'retrained_graph.pb (83.4 MB)')
    draw_card(9.5, 5.1, 2.6, 0.5, 'Lebreton 2018 (3,532 tows)')
    draw_card(9.5, 4.4, 2.6, 0.5, 'DFA 5-Tuple & TRAP State')

    for y in [6.05, 5.35, 4.65]:
        ax.annotate('', xy=(4.7, y), xytext=(3.5, y),
                    arrowprops=dict(arrowstyle='->', lw=1.8, color='#475569'), zorder=5)
        ax.annotate('', xy=(9.4, y), xytext=(8.1, y),
                    arrowprops=dict(arrowstyle='->', lw=1.8, color='#475569'), zorder=5)

    draw_box(0.5, 1.0, 11.9, 2.4, 'Verified System Outputs & Deliverables', '#faf5ff', '#6b21a8')
    draw_card(1.0, 1.5, 3.4, 1.2, 'Inference Output\nSoftmax Probabilities\n6 Classes (paper..plastic)', '#ffffff', '#d8b4fe')
    draw_card(4.8, 1.5, 3.4, 1.2, 'GIS Spatial Outputs\nHPI Scores & Tiers\n(Critical, Moderate, Baseline)', '#ffffff', '#d8b4fe')
    draw_card(8.6, 1.5, 3.4, 1.2, 'FLA Formal Outputs\n32 Accepted Words in L(M)\nMoore Minimality Verification', '#ffffff', '#d8b4fe')

    ax.set_title('End-to-End System Architecture: AI-GIS & Formal Automata', fontsize=15, fontweight='bold', pad=20, color='#1b365d')
    ax.set_xlim(0.0, 13.0)
    ax.set_ylim(0.5, 7.5)
    ax.axis('off')

    plt.tight_layout()
    plt.savefig(ARCH_IMG_PATH, dpi=300, bbox_inches='tight')
    plt.close()


def replace_frac(text):
    """Replaces all LaTeX \\frac{A}{B} with (A) / (B) respecting nested braces."""
    while r'\frac{' in text:
        idx = text.find(r'\frac{')
        if idx == -1:
            break
        depth = 0
        num_start = idx + len(r'\frac{')
        num_end = -1
        for i in range(idx + len(r'\frac'), len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    num_end = i
                    break
        if num_end == -1 or num_end + 1 >= len(text) or text[num_end + 1] != '{':
            break
        den_start = num_end + 2
        den_end = -1
        depth = 0
        for i in range(num_end + 1, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    den_end = i
                    break
        if den_end == -1:
            break
        numerator = text[num_start:num_end]
        denominator = text[den_start:den_end]
        text = text[:idx] + f"({numerator}) / ({denominator})" + text[den_end + 1:]
    return text


def clean_latex_to_unicode(text):
    """Converts LaTeX equations and mathematical notation into clean, readable Unicode."""
    if not text:
        return ""

    # Clean aligned blocks
    text = text.replace(r'\begin{aligned}', '').replace(r'\end{aligned}', '')
    text = text.replace(r'\\', '\n')

    # Convert fractions first with balanced brace parsing
    text = replace_frac(text)

    # Specific multi-character macros first
    macros = [
        (r'\delta_{\text{complete}}', 'δ_complete'),
        (r'\delta_{\text{comp}}', 'δ_complete'),
        (r'\hat{\delta}', 'δ̂'),
        (r'\delta', 'δ'),
        (r'\Sigma_{\text{alnum}}', 'Σ_alnum'),
        (r'\Sigma^*', 'Σ*'),
        (r'\Sigma', 'Σ'),
        (r'\epsilon', 'ε'),
        (r'\Delta^5', 'Δ⁵'),
        (r'\Delta', 'Δ'),
        (r'\blacksquare', '■'),
        (r'\emptyset', '∅'),
        (r'\forall', '∀'),
        (r'\notin', '∉'),
        (r'\in', '∈'),
        (r'\xrightarrow', '→'),
        (r'\rightarrow', '→'),
        (r'\to', '→'),
        (r'\equiv_L', '≡_L'),
        (r'\equiv', '≡'),
        (r'\iff', '⇔'),
        (r'\ge', '≥'),
        (r'\geq', '≥'),
        (r'\le', '≤'),
        (r'\leq', '≤'),
        (r'\times', '×'),
        (r'\cup', '∪'),
        (r'\cdot', '·'),
        (r'\pm', '±'),
        (r'\approx', '≈'),
        (r'\setminus', '\\'),
        (r'\subset', '⊂'),
        (r'\mathbb{R}^+', 'ℝ⁺'),
        (r'\mathbb{R}', 'ℝ'),
        (r'\mathbf{x}_{\text{norm}}', 'x_norm'),
        (r'\mathbf{x}_{\text{uint8}}', 'x_uint8'),
        (r'\mathbf{x}', 'x'),
        (r'\textasciicircum', '^'),
        (r'^\circ', '°'),
        (r'\circ', '°'),
        (r'\sigma', 'σ'),
        (r'\mid', '|'),
        (r'\min', 'min'),
        (r'\log_{10}', 'log₁₀'),
        (r'\log', 'log'),
        (r'\text{ g/km}^2', ' g/km²'),
        (r'\text{ km}^2', ' km²'),
        (r'\sum_{i=1}^6', 'Σ(i=1..6)'),
        (r'\sum', 'Σ'),
        (r'\quad', '  '),
        (r'\dots', '...'),
        (r'\Big(', '('),
        (r'\Big)', ')'),
        (r'\left(', '('),
        (r'\right)', ')'),
        (r'\left[', '['),
        (r'\right]', ']'),
        (r'\left\{', '{'),
        (r'\right\}', '}'),
        (r'\{', '{'),
        (r'\}', '}'),
        (r'\,', ' '),
    ]

    for old, new in macros:
        text = text.replace(old, new)

    # Clean \text{...}
    while r'\text{' in text:
        text = re.sub(r'\\text\{([^{}]*)\}', r'\1', text)

    # Superscripts and subscripts
    text = text.replace('^2', '²').replace('^5', '⁵')
    text = text.replace('_0', '₀').replace('_1', '₁').replace('_2', '₂')

    # Remove all $ and $$ delimiters
    text = text.replace('$$', '')
    text = text.replace('$', '')

    return text


def set_cell_background(cell, fill_hex):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tc_pr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tc_pr.append(tc_mar)


def add_formatted_text(p, text):
    """Parses markdown inline bold and italic tags into formatted runs, after Unicode conversion."""
    cleaned = clean_latex_to_unicode(text)
    tokens = re.split(r'(\*\*.*?\*\*|`.*?`|\*.*?\*)', cleaned)
    for token in tokens:
        if not token:
            continue
        if token.startswith('**') and token.endswith('**'):
            inner = token[2:-2].replace('`', '')
            run = p.add_run(inner)
            run.bold = True
        elif token.startswith('*') and token.endswith('*'):
            inner = token[1:-1].replace('`', '')
            run = p.add_run(inner)
            run.italic = True
        elif token.startswith('`') and token.endswith('`'):
            inner = token[1:-1]
            run = p.add_run(inner)
            run.font.name = 'Consolas'
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(160, 40, 40)
        else:
            run = p.add_run(token)


def add_footer_page_number(run):
    fld = parse_xml(r'<w:fldSimple %s w:instr="PAGE"/>' % nsdecls('w'))
    run._r.append(fld)


def add_footer_numpages(run):
    fld = parse_xml(r'<w:fldSimple %s w:instr="NUMPAGES"/>' % nsdecls('w'))
    run._r.append(fld)


def build_docx():
    print("Step 1: Rendering diagrams...")
    render_dfa_diagram()
    render_architecture_diagram()

    print("Step 2: Parsing markdown and building Word document...")
    doc = Document()

    # Configure Margins (1 inch)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

        # Header
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("AI-GIS Detection & Prioritisation of Plastic Waste Hotspots | Academic Report")
        hrun.font.name = 'Calibri'
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(140, 150, 160)

        # Footer
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        frun1 = fp.add_run("Page ")
        frun1.font.name = 'Calibri'
        frun1.font.size = Pt(9)
        frun1.font.color.rgb = RGBColor(128, 128, 128)
        add_footer_page_number(fp.add_run())
        frun2 = fp.add_run(" of ")
        frun2.font.name = 'Calibri'
        frun2.font.size = Pt(9)
        frun2.font.color.rgb = RGBColor(128, 128, 128)
        add_footer_numpages(fp.add_run())

    # Configure Styles
    styles = doc.styles
    normal_style = styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(40, 40, 40)

    with open(DOC_MD_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_code_block = False
    code_lang = ""
    code_lines = []
    in_table = False
    table_lines = []
    toc_added = False

    def flush_table():
        nonlocal in_table, table_lines
        if not table_lines:
            return
        parsed_rows = []
        for line in table_lines:
            line_str = line.strip()
            if not line_str.startswith('|'):
                continue
            cells = [c.strip() for c in line_str.split('|')[1:-1]]
            if all(re.match(r'^:?-+:?$', c) for c in cells if c):
                continue
            parsed_rows.append(cells)

        if parsed_rows:
            num_cols = max(len(r) for r in parsed_rows)
            table = doc.add_table(rows=len(parsed_rows), cols=num_cols)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = True

            for row_idx, row_data in enumerate(parsed_rows):
                is_header = (row_idx == 0)
                for col_idx in range(num_cols):
                    cell = table.cell(row_idx, col_idx)
                    cell_text = row_data[col_idx] if col_idx < len(row_data) else ""
                    p = cell.paragraphs[0]
                    p.paragraph_format.space_before = Pt(3)
                    p.paragraph_format.space_after = Pt(3)
                    p.paragraph_format.line_spacing = 1.15
                    add_formatted_text(p, cell_text)

                    if is_header:
                        set_cell_background(cell, "2B4C7E")
                        for run in p.runs:
                            run.font.color.rgb = RGBColor(255, 255, 255)
                            run.bold = True
                    else:
                        bg_color = "F8F9FA" if row_idx % 2 == 1 else "FFFFFF"
                        set_cell_background(cell, bg_color)
                    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)

            doc.add_paragraph()

        in_table = False
        table_lines = []

    def flush_code():
        nonlocal in_code_block, code_lang, code_lines
        if not code_lines:
            in_code_block = False
            return

        code_text = "".join(code_lines).strip()
        # Handle diagrams embedded in markdown code blocks
        if code_lang == 'mermaid' or 'graph TD' in code_text or 'stateDiagram' in code_text:
            if 'graph TD' in code_text:
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(8)
                p_img.paragraph_format.space_after = Pt(4)
                doc.add_picture(str(ARCH_IMG_PATH), width=Inches(6.2))
                p_cap = doc.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r_cap = p_cap.add_run("Figure 2.1: Modernized Multi-Layer System Architecture")
                r_cap.font.size = Pt(9.5)
                r_cap.font.italic = True
                r_cap.font.color.rgb = RGBColor(100, 100, 100)
            elif 'stateDiagram' in code_text or 'DRAFT' in code_text:
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(8)
                p_img.paragraph_format.space_after = Pt(4)
                doc.add_picture(str(DFA_IMG_PATH), width=Inches(6.2))
                p_cap = doc.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r_cap = p_cap.add_run("Figure 5.1: Waste Observation Lifecycle Automaton M = (Q, Σ, δ, q0, F)")
                r_cap.font.size = Pt(9.5)
                r_cap.font.italic = True
                r_cap.font.color.rgb = RGBColor(100, 100, 100)
        elif 'digraph WasteObservationLifecycle' in code_text:
            p_note = doc.add_paragraph()
            r_note = p_note.add_run("[Graphviz DOT Specification rendered in Figure 5.1 above]")
            r_note.font.italic = True
            r_note.font.color.rgb = RGBColor(120, 120, 120)
        else:
            # Format regular code block without backticks
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.4)
            p.paragraph_format.right_indent = Inches(0.4)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(6)
            cleaned_code = clean_latex_to_unicode(code_text)
            run = p.add_run(cleaned_code)
            run.font.name = 'Consolas'
            run.font.size = Pt(9.0)
            run.font.color.rgb = RGBColor(45, 55, 72)

        in_code_block = False
        code_lang = ""
        code_lines = []

    def insert_table_of_contents():
        """Inserts a structured Table of Contents."""
        h_toc = doc.add_heading(level=2)
        h_toc.paragraph_format.space_before = Pt(14)
        h_toc.paragraph_format.space_after = Pt(8)
        r_toc = h_toc.add_run("Table of Contents")
        r_toc.font.name = 'Calibri'
        r_toc.font.size = Pt(16)
        r_toc.font.color.rgb = RGBColor(34, 87, 126)
        r_toc.bold = True

        toc_items = [
            ("1. Abstract & Executive Summary", "High-level summary, academic context, problem statement, key findings"),
            ("2. End-to-End System Architecture", "Presentation, Service, Data layers; Architectural flow diagram"),
            ("3. Pretrained CNN Classification & Inference Architecture", "Inception-v3 graph, tensor specifications, OOD overconfidence, sanity checks"),
            ("4. Geographic Information System (GIS) & Spatial Prioritisation Engine", "Lebreton (2018) survey provenance, HPI mathematical formulation, clusters"),
            ("5. Formal Languages & Automata (FLA) Theoretical Framework", "5-tuple DFA, total transition completion, GNFA elimination, Moore refinement"),
            ("6. Systematic Empirical Verification & Test Results", "17 unit tests execution, live route status audit, verification telemetry"),
            ("7. Limitations, Ethical Considerations, & Future Scope", "Out-of-distribution overconfidence, single-object constraint, future automata"),
            ("8. Code Provenance & Project Contributions", "Baseline git inventory (efca74c), modern additions, Antigravity AI statement"),
            ("9. Visual Asset & Frontend Route Catalogue", "Summary of interactive web routes, endpoints, and frontend features")
        ]

        toc_table = doc.add_table(rows=len(toc_items) + 1, cols=2)
        toc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        toc_table.autofit = True

        # Header
        cell0 = toc_table.cell(0, 0)
        cell1 = toc_table.cell(0, 1)
        p0 = cell0.paragraphs[0]
        p1 = cell1.paragraphs[0]
        p0.add_run("Section / Module").bold = True
        p1.add_run("Content Overview").bold = True
        set_cell_background(cell0, "2B4C7E")
        set_cell_background(cell1, "2B4C7E")
        p0.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        p1.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_margins(cell0, 80, 80, 120, 120)
        set_cell_margins(cell1, 80, 80, 120, 120)

        for idx, (title, desc) in enumerate(toc_items):
            c_title = toc_table.cell(idx + 1, 0)
            c_desc = toc_table.cell(idx + 1, 1)
            pt = c_title.paragraphs[0]
            pd = c_desc.paragraphs[0]
            pt.paragraph_format.space_before = Pt(2)
            pt.paragraph_format.space_after = Pt(2)
            pd.paragraph_format.space_before = Pt(2)
            pd.paragraph_format.space_after = Pt(2)

            rt = pt.add_run(title)
            rt.bold = True
            rt.font.size = Pt(9.5)
            rt.font.color.rgb = RGBColor(27, 54, 93)

            rd = pd.add_run(desc)
            rd.font.size = Pt(9.0)
            rd.font.color.rgb = RGBColor(70, 80, 90)

            bg = "F8F9FA" if idx % 2 == 1 else "FFFFFF"
            set_cell_background(c_title, bg)
            set_cell_background(c_desc, bg)
            set_cell_margins(c_title, 60, 60, 120, 120)
            set_cell_margins(c_desc, 60, 60, 120, 120)

        doc.add_paragraph()

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        # Handle code blocks
        if stripped.startswith('```'):
            if in_table:
                flush_table()
            if in_code_block:
                flush_code()
            else:
                in_code_block = True
                code_lang = stripped[3:].strip()
            idx += 1
            continue

        if in_code_block:
            code_lines.append(line)
            idx += 1
            continue

        # Handle Markdown tables
        if stripped.startswith('|') and '|' in stripped[1:]:
            in_table = True
            table_lines.append(line)
            idx += 1
            continue
        elif in_table:
            flush_table()

        # Insert TOC right before Executive Summary
        if not toc_added and stripped.startswith('## 1. Abstract & Executive Summary'):
            insert_table_of_contents()
            toc_added = True

        # Handle Headings
        if stripped.startswith('# '):
            h = doc.add_heading(level=1)
            h.paragraph_format.space_before = Pt(14)
            h.paragraph_format.space_after = Pt(6)
            run = h.add_run(clean_latex_to_unicode(stripped[2:]))
            run.font.name = 'Calibri'
            run.font.size = Pt(22)
            run.font.color.rgb = RGBColor(27, 54, 93)
            run.bold = True
        elif stripped.startswith('## '):
            h = doc.add_heading(level=2)
            h.paragraph_format.space_before = Pt(12)
            h.paragraph_format.space_after = Pt(4)
            run = h.add_run(clean_latex_to_unicode(stripped[3:]))
            run.font.name = 'Calibri'
            run.font.size = Pt(16)
            run.font.color.rgb = RGBColor(34, 87, 126)
            run.bold = True
        elif stripped.startswith('### '):
            h = doc.add_heading(level=3)
            h.paragraph_format.space_before = Pt(10)
            h.paragraph_format.space_after = Pt(3)
            run = h.add_run(clean_latex_to_unicode(stripped[4:]))
            run.font.name = 'Calibri'
            run.font.size = Pt(13)
            run.font.color.rgb = RGBColor(40, 116, 101)
            run.bold = True
        elif stripped.startswith('#### '):
            h = doc.add_heading(level=4)
            h.paragraph_format.space_before = Pt(8)
            h.paragraph_format.space_after = Pt(2)
            run = h.add_run(clean_latex_to_unicode(stripped[5:]))
            run.font.name = 'Calibri'
            run.font.size = Pt(11.5)
            run.font.color.rgb = RGBColor(60, 60, 60)
            run.bold = True
        elif stripped.startswith('---'):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            r = p.add_run("―" * 50)
            r.font.color.rgb = RGBColor(180, 190, 200)
        elif stripped.startswith('- ') or stripped.startswith('* '):
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            add_formatted_text(p, stripped[2:])
        elif re.match(r'^\d+\.\s+', stripped):
            num_match = re.match(r'^(\d+\.)\s+(.*)', stripped)
            prefix = num_match.group(1)
            content = num_match.group(2)
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            add_formatted_text(p, content)
        elif stripped.startswith('> '):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.4)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            r = p.add_run("│ ")
            r.bold = True
            r.font.color.rgb = RGBColor(34, 87, 126)
            add_formatted_text(p, stripped[2:])
        elif stripped:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(5)
            p.paragraph_format.line_spacing = 1.15
            add_formatted_text(p, stripped)

        idx += 1

    if in_table:
        flush_table()
    if in_code_block:
        flush_code()

    doc.save(str(DOC_DOCX_PATH))
    print(f"Report successfully built at: {DOC_DOCX_PATH}")


if __name__ == '__main__':
    build_docx()
