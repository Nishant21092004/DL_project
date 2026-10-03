#!/usr/bin/env python3
"""Build docs/Repository_Guide.pdf from docs/Repository_Guide.md.

Dependency:
    pip install reportlab
"""
from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "Repository_Guide.md"
OUTPUT = ROOT / "docs" / "Repository_Guide.pdf"

NAVY = colors.HexColor("#17324D")
BLUE = colors.HexColor("#2367A6")
TEAL = colors.HexColor("#168C8C")
LIGHT_BLUE = colors.HexColor("#EAF3FA")
LIGHT_TEAL = colors.HexColor("#E9F7F5")
LIGHT_GREY = colors.HexColor("#F4F6F8")
MID_GREY = colors.HexColor("#667788")
DARK = colors.HexColor("#1E2933")
WHITE = colors.white

PAGE_BREAK_SECTIONS = {
    "3. High-level architecture",
    "6. Exact training flow",
    "8. Datasets and experimental setup",
    "9. Main results",
    "10. XAI and verification tools",
    "11. How to run the project",
    "13. What is implemented vs proposed",
    "15. Short explanation script",
}


def register_fonts() -> None:
    font_dir = Path("/usr/share/fonts/truetype/dejavu")
    pdfmetrics.registerFont(TTFont("GuideSans", str(font_dir / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("GuideSans-Bold", str(font_dir / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("GuideMono", str(font_dir / "DejaVuSansMono.ttf")))
    pdfmetrics.registerFont(TTFont("GuideMono-Bold", str(font_dir / "DejaVuSansMono-Bold.ttf")))
    pdfmetrics.registerFontFamily(
        "GuideSans",
        normal="GuideSans",
        bold="GuideSans-Bold",
        italic="GuideSans",
        boldItalic="GuideSans-Bold",
    )


def inline_markup(text: str) -> str:
    """Convert the small inline-Markdown subset used by the guide."""
    escaped = html.escape(text, quote=False)
    escaped = re.sub(
        r"`([^`]+)`",
        r'<font name="GuideMono" color="#155A8A">\1</font>',
        escaped,
    )
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", escaped)
    return escaped


def make_styles():
    base = getSampleStyleSheet()
    styles = {
        "body": ParagraphStyle(
            "GuideBody",
            parent=base["BodyText"],
            fontName="GuideSans",
            fontSize=9.1,
            leading=13.1,
            textColor=DARK,
            spaceAfter=5,
            alignment=TA_LEFT,
        ),
        "h1": ParagraphStyle(
            "GuideH1",
            parent=base["Heading1"],
            fontName="GuideSans-Bold",
            fontSize=21,
            leading=25,
            textColor=NAVY,
            spaceBefore=4,
            spaceAfter=12,
        ),
        "h2": ParagraphStyle(
            "GuideH2",
            parent=base["Heading2"],
            fontName="GuideSans-Bold",
            fontSize=15,
            leading=19,
            textColor=NAVY,
            spaceBefore=9,
            spaceAfter=7,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "GuideH3",
            parent=base["Heading3"],
            fontName="GuideSans-Bold",
            fontSize=11.5,
            leading=15,
            textColor=BLUE,
            spaceBefore=7,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "small": ParagraphStyle(
            "GuideSmall",
            parent=base["BodyText"],
            fontName="GuideSans",
            fontSize=7.7,
            leading=10.2,
            textColor=MID_GREY,
        ),
        "code": ParagraphStyle(
            "GuideCode",
            parent=base["Code"],
            fontName="GuideMono",
            fontSize=7.4,
            leading=10.3,
            leftIndent=6,
            rightIndent=6,
            borderColor=colors.HexColor("#D8E1E8"),
            borderWidth=0.5,
            borderPadding=7,
            backColor=LIGHT_GREY,
            textColor=colors.HexColor("#23313D"),
            spaceBefore=4,
            spaceAfter=8,
        ),
        "quote": ParagraphStyle(
            "GuideQuote",
            parent=base["BodyText"],
            fontName="GuideSans",
            fontSize=9.2,
            leading=13.5,
            leftIndent=12,
            rightIndent=10,
            borderColor=TEAL,
            borderWidth=2,
            borderPadding=9,
            backColor=LIGHT_TEAL,
            textColor=DARK,
            spaceBefore=5,
            spaceAfter=8,
        ),
        "toc": ParagraphStyle(
            "GuideTOC",
            parent=base["BodyText"],
            fontName="GuideSans",
            fontSize=9.1,
            leading=13,
            textColor=DARK,
            leftIndent=4,
        ),
        "table": ParagraphStyle(
            "GuideTable",
            parent=base["BodyText"],
            fontName="GuideSans",
            fontSize=7.2,
            leading=9.3,
            textColor=DARK,
        ),
        "table_header": ParagraphStyle(
            "GuideTableHeader",
            parent=base["BodyText"],
            fontName="GuideSans-Bold",
            fontSize=7.2,
            leading=9.3,
            textColor=WHITE,
        ),
    }
    return styles


def cover_page(story, styles) -> None:
    story.extend(
        [
            Spacer(1, 24 * mm),
            Paragraph("REPOSITORY GUIDE", ParagraphStyle(
                "CoverKicker", fontName="GuideSans-Bold", fontSize=11,
                leading=14, textColor=TEAL, alignment=TA_CENTER, spaceAfter=8,
            )),
            Paragraph(
                "XAI-Driven Modality Bias<br/>Detection and Mitigation",
                ParagraphStyle(
                    "CoverTitle", fontName="GuideSans-Bold", fontSize=27,
                    leading=34, textColor=NAVY, alignment=TA_CENTER, spaceAfter=14,
                ),
            ),
            HRFlowable(width="58%", thickness=2.2, color=TEAL, hAlign="CENTER", spaceAfter=14),
            Paragraph(
                "Concise Hinglish Technical Guide",
                ParagraphStyle(
                    "CoverSubtitle", fontName="GuideSans", fontSize=14,
                    leading=18, textColor=BLUE, alignment=TA_CENTER, spaceAfter=25,
                ),
            ),
        ]
    )

    summary = Paragraph(
        "<b>Core idea:</b> multimodal model me ek easy modality dominate kar sakti hai. "
        "Repository bias ko attribution aur discrepancy ratio se measure karti hai, "
        "phir OPM aur OGM-GE se dominant branch ko training ke dauran regulate karti hai.",
        styles["body"],
    )
    box = Table([[summary]], colWidths=[158 * mm])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#B9D4E8")),
        ("LEFTPADDING", (0, 0), (-1, -1), 13),
        ("RIGHTPADDING", (0, 0), (-1, -1), 13),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.extend([
        box,
        Spacer(1, 22 * mm),
        Paragraph(
            "IMPLEMENTED FOCUS",
            ParagraphStyle(
                "CoverLabel", fontName="GuideSans-Bold", fontSize=8.5,
                leading=11, textColor=MID_GREY, alignment=TA_CENTER,
            ),
        ),
        Spacer(1, 4 * mm),
    ])

    focus_data = [
        ["DETECT", "QUANTIFY", "MITIGATE", "VERIFY"],
        ["Attention + XAI", "Discrepancy rho", "OPM + OGM-GE", "Metrics + plots"],
    ]
    focus = Table(focus_data, colWidths=[39.5 * mm] * 4, rowHeights=[9 * mm, 11 * mm])
    focus.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "GuideSans-Bold"),
        ("FONTNAME", (0, 1), (-1, 1), "GuideSans"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B9C8D5")),
        ("BACKGROUND", (0, 1), (-1, 1), colors.white),
    ]))
    story.extend([
        focus,
        Spacer(1, 23 * mm),
        Paragraph(
            "Team: I24AI001 · I24AI009 · I24AI026 · I24AI028",
            ParagraphStyle(
                "CoverTeam", fontName="GuideSans", fontSize=9,
                leading=12, textColor=MID_GREY, alignment=TA_CENTER,
            ),
        ),
        Paragraph(
            "Repository snapshot: 3 October 2026",
            ParagraphStyle(
                "CoverDate", fontName="GuideSans", fontSize=8,
                leading=11, textColor=MID_GREY, alignment=TA_CENTER,
            ),
        ),
        PageBreak(),
    ])


def contents_page(story, styles, headings: list[str]) -> None:
    story.append(Paragraph("Contents", styles["h1"]))
    story.append(Paragraph(
        "Guide ko first-to-last read kiya ja sakta hai, ya specific section directly use kiya ja sakta hai.",
        styles["body"],
    ))
    left = headings[:8]
    right = headings[8:]
    rows = []
    for i in range(max(len(left), len(right))):
        a = Paragraph(inline_markup(left[i]), styles["toc"]) if i < len(left) else ""
        b = Paragraph(inline_markup(right[i]), styles["toc"]) if i < len(right) else ""
        rows.append([a, b])
    table = Table(rows, colWidths=[82 * mm, 82 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#E0E6EB")),
    ]))
    story.extend([Spacer(1, 4 * mm), table, Spacer(1, 8 * mm)])

    key = Table([
        [Paragraph("Fast reading path", styles["table_header"])],
        [Paragraph(
            "Sections 1 → 3 → 5 → 8 → 9 → 13 → 15 cover the complete project in the shortest path.",
            styles["body"],
        )],
    ], colWidths=[164 * mm])
    key.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("BACKGROUND", (0, 1), (-1, 1), LIGHT_TEAL),
        ("BOX", (0, 0), (-1, -1), 0.7, TEAL),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([key, PageBreak()])


def parse_table(lines: list[str], styles) -> Table:
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append(cells)
    if len(rows) >= 2 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in rows[1]):
        rows.pop(1)

    wrapped = []
    for row_index, row in enumerate(rows):
        style = styles["table_header"] if row_index == 0 else styles["table"]
        wrapped.append([Paragraph(inline_markup(cell), style) for cell in row])

    count = max(len(row) for row in wrapped)
    width = 164 * mm
    if count == 2:
        widths = [50 * mm, 114 * mm]
    elif count == 3:
        widths = [65 * mm, 49.5 * mm, 49.5 * mm]
    elif count == 4:
        widths = [51 * mm, 37.7 * mm, 37.7 * mm, 37.6 * mm]
    else:
        widths = [width / count] * count

    table = Table(wrapped, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CAD5DD")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def result_figures(story, styles) -> None:
    story.extend([PageBreak(), Paragraph("Benchmark figures", styles["h1"])])
    story.append(Paragraph(
        "Bars best validation accuracy dikhate hain. Exact mean ± standard deviation values Section 9 aur "
        "<font name='GuideMono'>balanced_mm/results/RESULTS.md</font> me available hain.",
        styles["body"],
    ))
    figures = [
        ("Synthetic benchmark", ROOT / "balanced_mm/results/bar_val_acc.png"),
        ("Food-101", ROOT / "balanced_mm/results/bar_val_acc_food101.png"),
        ("MELD", ROOT / "balanced_mm/results/bar_val_acc_meld.png"),
    ]
    for title, path in figures:
        if not path.exists():
            continue
        story.append(Paragraph(title, styles["h3"]))
        reader = ImageReader(str(path))
        pixel_w, pixel_h = reader.getSize()
        target_w = 158 * mm
        target_h = target_w * pixel_h / pixel_w
        if target_h > 57 * mm:
            target_h = 57 * mm
            target_w = target_h * pixel_w / pixel_h
        img = Image(str(path), width=target_w, height=target_h)
        img.hAlign = "CENTER"
        story.extend([img, Spacer(1, 2 * mm)])
    story.append(PageBreak())


def parse_markdown(text: str, styles) -> list:
    lines = text.splitlines()
    story = []
    paragraph_lines: list[str] = []
    inserted_figures = False

    def flush_paragraph() -> None:
        if not paragraph_lines:
            return
        joined = " ".join(line.strip().rstrip("  ") for line in paragraph_lines).strip()
        if joined:
            story.append(Paragraph(inline_markup(joined), styles["body"]))
        paragraph_lines.clear()

    i = 0
    in_code = False
    code_lines: list[str] = []
    first_h1_skipped = False
    while i < len(lines):
        line = lines[i]

        if line.startswith("```"):
            flush_paragraph()
            if in_code:
                story.append(Preformatted("\n".join(code_lines), styles["code"] , maxLineLength=105))
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue

        if line.startswith("# "):
            flush_paragraph()
            if not first_h1_skipped:
                first_h1_skipped = True
            else:
                story.append(Paragraph(inline_markup(line[2:].strip()), styles["h1"]))
            i += 1
            continue
        if line.startswith("## "):
            flush_paragraph()
            heading = line[3:].strip()
            if heading == "XAI-Driven Modality Bias Detection and Mitigation":
                i += 1
                continue
            if heading == "10. XAI and verification tools" and not inserted_figures:
                result_figures(story, styles)
                inserted_figures = True
            if heading in PAGE_BREAK_SECTIONS and story and not (
                heading == "10. XAI and verification tools" and inserted_figures
            ):
                story.append(PageBreak())
            story.append(Paragraph(inline_markup(heading), styles["h2"]))
            i += 1
            continue
        if line.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[4:].strip()), styles["h3"]))
            i += 1
            continue
        if line.strip() == "---":
            flush_paragraph()
            story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#D6DEE5"), spaceBefore=4, spaceAfter=7))
            i += 1
            continue

        if line.startswith("> "):
            flush_paragraph()
            quote_lines = []
            while i < len(lines) and lines[i].startswith("> "):
                quote_lines.append(lines[i][2:].strip())
                i += 1
            story.append(Paragraph(inline_markup(" ".join(quote_lines)), styles["quote"]))
            continue

        if line.startswith("| "):
            flush_paragraph()
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            story.extend([parse_table(table_lines, styles), Spacer(1, 3 * mm)])
            continue

        bullet_match = re.match(r"^-\s+(.*)", line)
        number_match = re.match(r"^(\d+)\.\s+(.*)", line)
        if bullet_match or number_match:
            flush_paragraph()
            ordered = bool(number_match)
            items = []
            while i < len(lines):
                match = re.match(r"^(\d+)\.\s+(.*)", lines[i]) if ordered else re.match(r"^-\s+(.*)", lines[i])
                if not match:
                    break
                content = match.group(2) if ordered else match.group(1)
                items.append(ListItem(Paragraph(inline_markup(content), styles["body"]), leftIndent=8))
                i += 1
            list_options = {
                "bulletType": "1" if ordered else "bullet",
                "leftIndent": 19,
                "bulletFontName": "GuideSans-Bold",
                "bulletFontSize": 8,
                "spaceAfter": 5,
            }
            if ordered:
                list_options["start"] = "1"
            story.append(ListFlowable(items, **list_options))
            continue

        if not line.strip():
            flush_paragraph()
        elif line.startswith("**Project type:**") or line.startswith("**Team:**") or line.startswith("**Core stack:**"):
            # Metadata is already represented on the designed cover.
            pass
        else:
            paragraph_lines.append(line)
        i += 1

    flush_paragraph()
    return story


def page_decorations(canvas, doc) -> None:
    canvas.saveState()
    page = canvas.getPageNumber()
    width, height = A4
    if page > 1:
        canvas.setStrokeColor(colors.HexColor("#D9E1E7"))
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, height - 24 * mm, width - doc.rightMargin, height - 24 * mm)
        canvas.setFont("GuideSans", 7.2)
        canvas.setFillColor(MID_GREY)
        canvas.drawString(doc.leftMargin, height - 20.5 * mm, "DL Project · Repository Guide")
        canvas.drawRightString(width - doc.rightMargin, height - 20.5 * mm, "Modality Bias Detection & Mitigation")

    canvas.setStrokeColor(colors.HexColor("#D9E1E7"))
    canvas.line(doc.leftMargin, 16 * mm, width - doc.rightMargin, 16 * mm)
    canvas.setFont("GuideSans", 7.2)
    canvas.setFillColor(MID_GREY)
    canvas.drawString(doc.leftMargin, 11 * mm, "Nishant21092004/DL_project")
    canvas.drawRightString(width - doc.rightMargin, 11 * mm, f"Page {page}")
    canvas.restoreState()


def build() -> Path:
    register_fonts()
    styles = make_styles()
    markdown = SOURCE.read_text(encoding="utf-8")
    headings = [
        line[3:].strip()
        for line in markdown.splitlines()
        if line.startswith("## ")
        and line[3:].strip() != "XAI-Driven Modality Bias Detection and Mitigation"
    ]

    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=23 * mm,
        leftMargin=23 * mm,
        topMargin=29 * mm,
        bottomMargin=21 * mm,
        title="Repository Guide — XAI-Driven Modality Bias Detection and Mitigation",
        author="DL Project Team: I24AI001, I24AI009, I24AI026, I24AI028",
        subject="Technical explanation of the DL_project repository",
        creator="ReportLab",
    )

    story = []
    cover_page(story, styles)
    contents_page(story, styles, headings)
    story.extend(parse_markdown(markdown, styles))
    document.build(story, onFirstPage=page_decorations, onLaterPages=page_decorations)
    return OUTPUT


if __name__ == "__main__":
    output = build()
    print(f"wrote {output} ({output.stat().st_size / 1024:.1f} KiB)")
