#!/usr/bin/env bash
set -euo pipefail
echo "[CI] Install TeX Live (if needed handled in workflow)"
mkdir -p out
latexmk -pdf -interaction=nonstopmode -halt-on-error -shell-escape -outdir=out paper/paper.tex
echo "[CI] Built out/paper.pdf"
