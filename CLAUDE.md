# Project conventions

## Language

Write everything that ends up in the repository in **English**: README and other Markdown docs, generated
reports (`scripts/test_report.py`), code comments, docstrings, log/CLI output, commit messages and PR descriptions.
Chat with the user may stay in German.

## Docs that must stay in sync

* `docs/test-report.md` is generated – never edit it by hand; change `scripts/test_report.py` and regenerate
  (commands in the report's *Reproduce* section). Regenerate after committing so it references a clean commit.
* The performance table in `README.md` summarizes the report; update it when the benchmark numbers change.
* New searchable attributes need an Oracle multivalue index (see `alembic/versions/7c2e5b1a9f40_add_payload_indexes.py`
  and `a4f1c3d2e8b7_add_reference_indexes.py`); PostgreSQL is covered by the GIN index.
