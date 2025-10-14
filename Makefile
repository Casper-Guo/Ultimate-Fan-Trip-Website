.PHONY: serve

serve:
	bundle exec jekyll serve --source docs

all:
	python3 src/converter.py data/2025-2026/mlb
	python3 src/converter.py data/2025-2026/nba
	python3 src/converter.py data/2025-2026/nhl
	bundle exec jekyll serve --source docs
