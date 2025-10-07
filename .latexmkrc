# Fast, reliable builds with latexmk
$pdf_mode = 1;          # pdflatex
$interaction = 'nonstopmode';
$halt_on_error = 0;
$silent = 1;

# Retry bib/refs if needed
$bibtex_use = 2;

# Good defaults
$ENV{'max_print_line'} = 1000;
$aux_dir = 'build';
$out_dir = 'build';

# Cleanup extras on `latexmk -C`
@generated_exts = (@generated_exts, 'run.xml','bcf','bbl','blg','synctex.gz');

# Allow shell-escape only if you really need it:
$pdflatex = 'pdflatex -file-line-error -synctex=1 %O %S';
