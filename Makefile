PY        ?= python3
EPUBCHECK ?= epubcheck
LUALATEX  ?= lualatex
EDITION   ?= erstausgaben
VARIANT   ?=
BANDS     ?= 1 2 3

empty   :=
space   := $(empty) $(empty)
OUT     := build/$(EDITION)$(if $(VARIANT),-$(subst $(space),-,$(VARIANT)))
EPUBS   := $(foreach b,$(BANDS),$(OUT)/kapital-$(b).epub)
EPOCH   := $(shell git log -1 --format=%ct 2>/dev/null)
VERSION ?= $(shell git describe --tags --dirty 2>/dev/null)
ED      := editions/$(EDITION)
OPTS    := -e $(EDITION) $(foreach v,$(VARIANT),-v $(v))
SOURCES := tei2epub.py tables.py kapital.css \
           $(wildcard $(ED)/*.py) $(wildcard $(ED)/tables/*/*.txt) \
           $(wildcard variants/*.py) $(wildcard variants/*.json)
DATEENV := $(if $(EPOCH),SOURCE_DATE_EPOCH=$(EPOCH)) \
           $(if $(VERSION),KAPITAL_VERSION=$(VERSION))
TEXENV  := TEXINPUTS=.:$(CURDIR)/latex: TTFONTS=$(CURDIR)/latex/fonts: \
           $(if $(EPOCH),$(DATEENV) FORCE_SOURCE_DATE=1)

.PHONY: all check pdf covers jackets clean

all: $(EPUBS)

$(OUT)/kapital-%.epub: $(SOURCES)
	@mkdir -p $(OUT)
	$(DATEENV) $(PY) tei2epub.py $(OPTS) $* $@

check: $(EPUBS)
	for f in $^; do $(EPUBCHECK) --failonwarnings "$$f" || exit 1; done

# PDF über LuaLaTeX (braucht die deutschen und griechischen Trennmuster; die
# Schriften liegen in latex/fonts)
pdf:
	@mkdir -p $(OUT)/tex
	for b in $(BANDS); do \
	  rm -f $(OUT)/tex/kapital-$$b.tex $(OUT)/tex/kapital-$$b-?.tex; \
	  $(DATEENV) $(PY) tei2tex.py $(OPTS) $$b $(OUT)/tex/kapital-$$b.tex \
	    || exit 1; \
	done
	cd $(OUT)/tex && for b in $(BANDS); do \
	  files=$$(ls kapital-$$b.tex kapital-$$b-?.tex 2>/dev/null); \
	  for i in 1 2; do for f in $$files; do \
	    $(TEXENV) $(LUALATEX) -interaction=batchmode -halt-on-error $$f \
	      || { tail -n 30 $${f%.tex}.log; exit 1; }; \
	  done; done; \
	  for f in $$files; do cp $${f%.tex}.pdf ..; done; \
	  $(PY) $(CURDIR)/tools/check_tex_log.py \
	    $$(echo $$files | sed 's/\.tex/.log/g') || exit 1; \
	done

# Umschläge neu rendern (braucht Node.js; einmalig:
# cd tools && npm ci && npx playwright install chromium)
covers:
	node tools/render_covers.js $(ED)

# Schutzumschläge für Lulu; die Rückenbreite folgt aus der Seitenzahl, daher
# erst nach make pdf
jackets:
	cd $(OUT)/tex && for p in $$($(PY) -c 'import json, sys; \
	    print(*json.load(open(sys.argv[1]))["volumes"])' \
	    $(CURDIR)/$(ED)/jackets.json); do \
	  [ -f kapital-$$p.log ] || continue; \
	  $(PY) $(CURDIR)/tools/mk_jacket.py $(CURDIR)/$(ED)/jackets.json $$p \
	    kapital-$$p.log '$(VARIANT)' umschlag-$$p.tex || exit 1; \
	  for i in 1 2; do \
	    $(TEXENV) $(LUALATEX) -interaction=batchmode -halt-on-error \
	      umschlag-$$p.tex || { tail -n 30 umschlag-$$p.log; exit 1; }; \
	  done; \
	  $(PY) $(CURDIR)/tools/check_tex_log.py umschlag-$$p.log || exit 1; \
	  cp umschlag-$$p.pdf ../kapital-$$p-umschlag.pdf; \
	done

clean:
	rm -rf build
