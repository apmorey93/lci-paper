#!/usr/bin/env python3
"""Produce a lightweight textual diff when latexdiff is unavailable."""

from __future__ import annotations

import argparse
import difflib
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a plain-text diff for TeX files.")
    parser.add_argument("old", type=Path, help="Path to the old TeX file")
    parser.add_argument("new", type=Path, help="Path to the new TeX file")
    parser.add_argument("output", type=Path, help="Destination file for the textual diff")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    old_lines = args.old.read_text(encoding="utf-8").splitlines()
    new_lines = args.new.read_text(encoding="utf-8").splitlines()
    diff_lines = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=str(args.old),
            tofile=str(args.new),
            lineterm="",
        )
    )
    if not diff_lines:
        diff_lines = ["No differences detected."]
    args.output.write_text("\n".join(diff_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
