DOC=lci_paper
BUILD=build
PDF=$(BUILD)/$(DOC).pdf
DIFF_OUT=$(BUILD)/$(DOC)-diff.pdf
PYTHON ?= python3
FALLBACK=$(PYTHON) scripts/fallback_pdf.py

.PHONY: all pdf clean clobber diff lint

all: pdf

$(PDF): $(DOC).tex | $(BUILD)
	@if command -v latexmk >/dev/null 2>&1; then \
		latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=$(BUILD) $(DOC).tex; \
	elif command -v tectonic >/dev/null 2>&1; then \
		tectonic --keep-logs --synctex --outdir $(BUILD) $(DOC).tex; \
	else \
		$(FALLBACK) $(DOC).tex $(PDF); \
	fi
	@echo "PDF -> $(PDF)"

pdf: $(PDF)

$(BUILD):
	@mkdir -p $(BUILD)

clean:
	@if command -v latexmk >/dev/null 2>&1; then \
		latexmk -c -outdir=$(BUILD) $(DOC).tex; \
	fi
	@rm -f $(PDF)

clobber:
	@if command -v latexmk >/dev/null 2>&1; then \
		latexmk -C -outdir=$(BUILD) $(DOC).tex; \
	fi
	@rm -rf $(BUILD)

# latexdiff target (requires two git refs)
# usage: make diff OLD=origin/main NEW=HEAD
diff: | $(BUILD)
	@test -n "$(OLD)" && test -n "$(NEW)" || (echo "Usage: make diff OLD=<ref> NEW=<ref>"; exit 1)
	@git show $(OLD):$(DOC).tex > $(BUILD)/$(DOC)-old.tex
	@git show $(NEW):$(DOC).tex > $(BUILD)/$(DOC)-new.tex
	@if command -v latexdiff >/dev/null 2>&1; then \
		latexdiff $(BUILD)/$(DOC)-old.tex $(BUILD)/$(DOC)-new.tex > $(BUILD)/$(DOC)-diff.tex; \
	else \
		echo "latexdiff not found; using unified diff fallback."; \
		$(PYTHON) scripts/fallback_latexdiff.py $(BUILD)/$(DOC)-old.tex $(BUILD)/$(DOC)-new.tex $(BUILD)/$(DOC)-diff.tex; \
	fi
	@if command -v latexmk >/dev/null 2>&1; then \
		latexmk -pdf -silent -outdir=$(BUILD) $(BUILD)/$(DOC)-diff.tex; \
	elif command -v tectonic >/dev/null 2>&1; then \
		tectonic --keep-logs --synctex --outdir=$(BUILD) $(BUILD)/$(DOC)-diff.tex; \
	else \
		$(FALLBACK) $(BUILD)/$(DOC)-diff.tex $(DIFF_OUT); \
	fi
	@echo "Diff PDF -> $(DIFF_OUT)"

lint:
	chktex -q -n1 -n8 -n36 $(DOC).tex || true
