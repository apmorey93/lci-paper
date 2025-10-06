#!/usr/bin/env bash
set -euo pipefail
echo "[ci_build] generating tables"
bash scripts/build_tables.sh
echo "[ci_build] building LaTeX"
mkdir -p out
latexmk -pdf -interaction=nonstopmode -halt-on-error -shell-escape -outdir=out paper/paper.tex
ls -l out || true
