# Canonical developer commands. `make check` is the one repeatable health baseline.
.PHONY: check check-fast test web install help

help:
	@echo "make check       backend tests + doc-consistency + web build (the full baseline)"
	@echo "make check-fast  backend tests + doc-consistency only (skip the Vite build)"
	@echo "make test        backend unit tests only (pytest)"
	@echo "make web         frontend production build only"
	@echo "make install     install runtime + dev Python deps"

check:
	@bash scripts/check.sh

check-fast:
	@SKIP_WEB=1 bash scripts/check.sh

test:
	@python3 -m pytest

web:
	@npm --prefix web run build

install:
	@pip install -r requirements.txt -r requirements-dev.txt
