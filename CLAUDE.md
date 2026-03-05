# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sphinx documentation site for SMACC2 (State Machine Asynchronous C++ for ROS2), hosted on Read the Docs. Uses the `sphinx_rtd_theme`.

## Build Commands

```bash
# Install dependencies
pip install -r docs/requirements.txt

# Build HTML locally
cd docs && make html
# Or directly:
sphinx-build -b html docs/source docs/build/html

# Clean build
cd docs && make clean && make html
```

The site is auto-built by Read the Docs on push to `main` (configured in `.readthedocs.yaml`).

## Architecture

- **`.readthedocs.yaml`** — RTD build config (Ubuntu 22.04, Python 3.10)
- **`docs/source/conf.py`** — Sphinx configuration (theme, extensions, project metadata)
- **`docs/source/index.rst`** — Root document with hidden toctree defining page order
- **`docs/source/*.rst`** — Content pages (reStructuredText)
- **`docs/source/images/`** — Static images referenced from RST files
- **`docs/source/_templates/layout.html`** — Custom footer extending RTD theme (Matomo + GA analytics)
- **`docs/requirements.txt`** — Python deps: `sphinx==7.1.2`, `sphinx-rtd-theme==1.3.0rc1`

## Document Tree (defined in index.rst toctree)

`getting started` → `concepts1` → `concepts2` → `repositories` → `debians` → `demos` → `documentation` → `forums` → `troubleshooting` → `about` → `research group` → `other resources` → `citations`

The substantive technical content is in `concepts1.rst` (HSM architecture, state functions, transitions) and `concepts2.rst` (substates, orthogonals, events, threading model). Most other pages are link collections or stubs.

## Known Issues

- `lumache.py`, `pyproject.toml`, and `README.rst` are leftover boilerplate from the Read the Docs tutorial template — not related to SMACC2
- `release notes.rst` exists on disk but is not in the toctree and still contains tutorial boilerplate
- `layout.html` has a placeholder Google Analytics ID (`G-XXXXXXXXXX`); Matomo is properly configured
- Several images in `images/` are not referenced by any RST file
