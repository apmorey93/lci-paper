DOC=lci_paper
BUILD=build
PDF=$(BUILD)/$(DOC).pdf
DIFF_OUT=$(BUILD)/$(DOC)-diff.pdf

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
	@git show $(OLD):$(DOC).tex > /tmp/old.tex
	@git show $(NEW):$(DOC).tex > /tmp/new.tex
	@latexdiff /tmp/old.tex /tmp/new.tex > $(BUILD)/$(DOC)-diff.tex
	@latexmk -pdf -silent $(BUILD)/$(DOC)-diff.tex
	@echo "Diff PDF -> $(DIFF_OUT)"

lint:
	chktex -q -n1 -n8 -n36 $(DOC).tex || true
