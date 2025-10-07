DOC=lci_paper
BUILD=build
PDF=$(BUILD)/$(DOC).pdf
DIFF_TEX=$(BUILD)/$(DOC)-diff.tex
DIFF_OUT=$(BUILD)/$(DOC)-diff.pdf
PYTHON ?= python3
FALLBACK ?= $(PYTHON) scripts/fallback_pdf.py
FALLBACK_DIFF ?= $(PYTHON) scripts/fallback_latexdiff.py

.PHONY: all pdf clean clobber diff lint

all: pdf

pdf:
	latexmk -pdf -silent $(DOC).tex
	@echo "PDF -> $(PDF)"

clean:
	latexmk -c

clobber:
	latexmk -C
	rm -rf $(BUILD)

# latexdiff target (requires two git refs)
# usage: make diff OLD=origin/main NEW=HEAD
diff:
	@test -n "$(OLD)" && test -n "$(NEW)" || (echo "Usage: make diff OLD=<ref> NEW=<ref>"; exit 1)
	@mkdir -p $(BUILD)
	@git show $(OLD):$(DOC).tex > /tmp/old.tex
	@git show $(NEW):$(DOC).tex > /tmp/new.tex
	@RAN_REAL_DIFF=0; \
	if command -v latexdiff >/dev/null 2>&1; then \
		RAN_REAL_DIFF=1; \
		latexdiff /tmp/old.tex /tmp/new.tex > $(DIFF_TEX); \
	else \
		echo "latexdiff unavailable; using textual fallback."; \
		$(FALLBACK_DIFF) /tmp/old.tex /tmp/new.tex $(DIFF_TEX); \
		$(FALLBACK) $(DIFF_TEX) $(DIFF_OUT); \
		echo "Fallback diff PDF (textual) -> $(DIFF_OUT)"; \
	fi; \
	if [ $$RAN_REAL_DIFF -eq 1 ]; then \
		latexmk -pdf -silent $(DIFF_TEX); \
		echo "Diff PDF -> $(DIFF_OUT)"; \
	fi

lint:
	chktex -q -n1 -n8 -n36 $(DOC).tex || true
