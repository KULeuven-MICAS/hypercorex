import os
import sys
sys.path.insert(0, os.path.abspath('../..'))  # adjust path to your project root

project = 'VSAX'
copyright = '2026, Ryan Antonio'
author = 'Ryan Antonio'
release = '0.1.0'

# ── General settings ─────────────────────────────────────────────────────────
extensions = [
    'sphinx.ext.autodoc',           # reads your docstrings
    'sphinx.ext.napoleon',          # supports Google/NumPy style docstrings
    'sphinx.ext.viewcode',          # adds links to source code
    'sphinx_autodoc_typehints',     # renders type hints nicely
    'myst_parser',
]

# ── Theme settings ───────────────────────────────────────────────────────────
html_theme = 'furo'

# ── Autodoc settings ─────────────────────────────────────────────────────────
autodoc_member_order = 'bysource'   # keeps the order as written in your file
autodoc_typehints = 'description'   # shows type hints in the description

# ── Sourcefile settings ──────────────────────────────────────────────────────
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# ── Warning settings ─────────────────────────────────────────────────────────
suppress_warnings = ["myst.xref_missing"]