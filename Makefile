# Canonical developer commands. `make check` is the one repeatable health baseline.
.PHONY: check check-fast test web install seed-demo help

help:
	@echo "make check       backend tests + doc-consistency + web build (the full baseline)"
	@echo "make check-fast  backend tests + doc-consistency only (skip the Vite build)"
	@echo "make test        backend unit tests only (pytest)"
	@echo "make web         frontend production build only"
	@echo "make seed-demo   populate bids.db with illustrative demo data (Plan → the rest)"
	@echo "make install     install runtime + dev Python deps"

check:
	@bash scripts/check.sh

check-fast:
	@SKIP_WEB=1 bash scripts/check.sh

test:
	@python3 -m pytest

web:
	@npm --prefix web run build

# Demo data for the stage boards. Plan MUST run first — Complete/Manage/Learn hang
# their rows off the bids the Plan seed creates. All upserts are keyed, so re-running
# updates in place rather than duplicating.
seed-demo:
	@echo "Seeding demo data (Plan first — the others attach to its bids)…"
	@python3 src/seed_plan_demo.py
	@python3 src/seed_complete_demo.py
	@python3 src/seed_manage_demo.py
	@python3 src/seed_learn_demo.py

install:
	@pip install -r requirements.txt -r requirements-dev.txt
