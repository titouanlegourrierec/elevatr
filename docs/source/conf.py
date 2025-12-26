"""Configuration file for the Sphinx documentation builder."""  # noqa: INP001

import re
import sys
from pathlib import Path


sys.path.insert(0, str(Path("../../").resolve()))

# -- Project information -----------------------------------------------------

author = "Titouan Le Gourrierec"
copyright = "2025, Titouan Le Gourrierec"  # noqa: A001
project = "elevatr"


pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
with pyproject_path.open() as f:
    content = f.read()
match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)


# The full version, including alpha/beta/rc tags
version = release = match.group(1) if match else "unknown"


# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
]

templates_path = ["_templates"]
exclude_patterns: list[str] = []


# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_favicon = "_static/favicon.ico"
html_static_path = ["_static"]
html_show_sourcelink = False

# -- Options for autodoc -------------------------------------------------

autodoc_typehints = "description"
autodoc_member_order = "bysource"
autodoc_inherit_docstrings = False

# -- Options for napoleon -------------------------------------------------

napoleon_numpy_docstring = True
