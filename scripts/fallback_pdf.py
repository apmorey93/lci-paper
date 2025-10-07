#!/usr/bin/env python3
"""Minimal PDF renderer for environments without a LaTeX toolchain.

The script degrades gracefully by extracting plain text from a TeX source
and emitting a simple multi-page PDF using built-in Type1 fonts. It preserves
section headings and paragraph breaks, escaping math macros to keep the text
readable. The output is not typographically perfect but ensures `make pdf`
finishes successfully even when `latexmk`/`pdflatex` are unavailable.
"""

from __future__ import annotations

import argparse
import re
import textwrap
from pathlib import Path
from typing import Iterable

PDF_HEADER = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
PAGE_WIDTH = 612  # 8.5in * 72pt
PAGE_HEIGHT = 792  # 11in * 72pt
LEFT_MARGIN = 72
TOP_MARGIN = PAGE_HEIGHT - 72
LINE_HEIGHT = 14
MAX_LINES_PER_PAGE = int((TOP_MARGIN - 72) / LINE_HEIGHT)

COMMAND_PATTERNS = {
    r"\\section\*?\{([^}]*)\}": lambda m: f"\n\n{m.group(1).upper()}\n",
    r"\\subsection\*?\{([^}]*)\}": lambda m: f"\n\n{m.group(1)}\n",
    r"\\subsubsection\*?\{([^}]*)\}": lambda m: f"\n\n{m.group(1)}\n",
    r"\\paragraph\*?\{([^}]*)\}": lambda m: f"\n\n{m.group(1)}\n",
}

MATH_PLACEHOLDER = "[math]"


def strip_comments(tex: str) -> str:
    cleaned_lines = []
    for line in tex.splitlines():
        if "\\%" in line:
            # Protect escaped percent signs by temporary token
            line = line.replace("\\%", "<PERCENT>")
        if "%" in line:
            line = line.split("%", 1)[0]
        cleaned_lines.append(line.replace("<PERCENT>", "%"))
    return "\n".join(cleaned_lines)


def normalize_commands(tex: str) -> str:
    result = tex
    for pattern, replacer in COMMAND_PATTERNS.items():
        result = re.sub(pattern, replacer, result)
    return result


def remove_environments(tex: str) -> str:
    return re.sub(r"\\begin\{[^}]*\}|\\end\{[^}]*\}", "\n", tex)


def strip_inline_math(tex: str) -> str:
    tex = re.sub(r"\\\(|\\\)", " ", tex)
    tex = re.sub(r"\\\[|\\\]", " ", tex)
    tex = re.sub(r"\$\$.*?\$\$", MATH_PLACEHOLDER, tex, flags=re.S)
    tex = re.sub(r"\$[^$]*\$", MATH_PLACEHOLDER, tex)
    return tex


def strip_commands(tex: str) -> str:
    tex = re.sub(r"\\[a-zA-Z@]+\*?\s*", " ", tex)
    tex = tex.replace("{", " ").replace("}", " ")
    tex = re.sub(r"~", " ", tex)
    tex = re.sub(r"\\", " ", tex)
    return tex


def collapse_whitespace(tex: str) -> list[str]:
    lines: list[str] = []
    for raw_line in tex.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            lines.append("")
            continue
        wrapped = textwrap.wrap(stripped, width=90) or [""]
        lines.extend(wrapped)
    # Reduce consecutive blank lines to at most two
    normalized: list[str] = []
    blank_run = 0
    for line in lines:
        if line.strip():
            blank_run = 0
            normalized.append(line)
        else:
            blank_run += 1
            if blank_run <= 2:
                normalized.append("")
    return normalized or ["(empty document)"]


def sanitize_for_pdf(text: str) -> str:
    return (
        text.replace("\\", r"\\\\")
        .replace("(", r"\\(")
        .replace(")", r"\\)")
    )


def chunk_lines(lines: Iterable[str]) -> list[list[str]]:
    chunk: list[str] = []
    pages: list[list[str]] = []
    for line in lines:
        if len(chunk) >= MAX_LINES_PER_PAGE:
            pages.append(chunk)
            chunk = []
        chunk.append(line)
    if chunk:
        pages.append(chunk)
    return pages


def build_content_stream(lines: list[str]) -> bytes:
    instructions = ["BT", "/F1 11 Tf", f"{LINE_HEIGHT} TL", f"{LEFT_MARGIN} {TOP_MARGIN} Td"]
    for idx, line in enumerate(lines):
        safe = sanitize_for_pdf(line)
        if idx == 0:
            instructions.append(f"({safe}) Tj")
        else:
            instructions.extend(["T*", f"({safe}) Tj"])
    instructions.append("ET")
    stream_body = "\n".join(instructions).encode("utf-8")
    return (
        f"<< /Length {len(stream_body)} >>\n".encode("ascii")
        + b"stream\n"
        + stream_body
        + b"\nendstream"
    )


def write_pdf(lines: list[str], output_path: Path) -> None:
    pages = chunk_lines(lines)
    objects: list[bytes | None] = [None, None]  # placeholders for catalog & pages

    font_obj_num = add_object(objects, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_obj_nums: list[int] = []
    for page_lines in pages:
        content_obj_num = add_object(objects, build_content_stream(page_lines))
        page_dict = (
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {w} {h}] "
            "/Resources << /Font << /F1 {font_ref} 0 R >> >> "
            "/Contents {content_ref} 0 R >>"
        ).format(w=PAGE_WIDTH, h=PAGE_HEIGHT, font_ref=font_obj_num, content_ref=content_obj_num)
        page_obj_nums.append(add_object(objects, page_dict.encode("ascii")))

    kids_entries = " ".join(f"{num} 0 R" for num in page_obj_nums)
    pages_dict = f"<< /Type /Pages /Count {len(page_obj_nums)} /Kids [{kids_entries}] >>".encode("ascii")
    objects[1] = pages_dict
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"

    write_objects(output_path, objects)


def add_object(objects: list[bytes | None], data: bytes) -> int:
    objects.append(data)
    return len(objects)


def write_objects(output_path: Path, objects: list[bytes | None]) -> None:
    offsets: list[int] = [0]
    with output_path.open("wb") as fh:
        fh.write(PDF_HEADER)
        for obj_number, data in enumerate(objects, start=1):
            if data is None:
                raise ValueError(f"Missing object body for index {obj_number}")
            offsets.append(fh.tell())
            fh.write(f"{obj_number} 0 obj\n".encode("ascii"))
            fh.write(data)
            fh.write(b"\nendobj\n")
        xref_offset = fh.tell()
        fh.write(f"xref\n0 {len(objects)+1}\n".encode("ascii"))
        fh.write(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            fh.write(f"{offset:010d} 00000 n \n".encode("ascii"))
        fh.write(b"trailer\n")
        fh.write(f"<< /Root 1 0 R /Size {len(objects)+1} >>\n".encode("ascii"))
        fh.write(b"startxref\n")
        fh.write(f"{xref_offset}\n".encode("ascii"))
        fh.write(b"%%EOF\n")


def extract_plaintext(tex_path: Path) -> list[str]:
    raw = tex_path.read_text(encoding="utf-8")
    pipeline = strip_comments(raw)
    pipeline = normalize_commands(pipeline)
    pipeline = remove_environments(pipeline)
    pipeline = strip_inline_math(pipeline)
    pipeline = strip_commands(pipeline)
    lines = collapse_whitespace(pipeline)
    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render TeX to a basic PDF without LaTeX.")
    parser.add_argument("source", type=Path, help="Input .tex file")
    parser.add_argument("output", type=Path, help="Output PDF path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output.parent
    if output_dir and not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    lines = extract_plaintext(args.source)
    write_pdf(lines, args.output)

    print(f"Fallback PDF -> {args.output}")


if __name__ == "__main__":
    main()
