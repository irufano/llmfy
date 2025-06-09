from dataclasses import asdict
import os
import sys

from dotenv import load_dotenv
from sphinxawesome_theme import ThemeOptions

load_dotenv()

sys.path.insert(0, os.path.abspath("../../"))


# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information


project = "llmfy_docs"
# copyright = "2025, irufano"
author = "irufano"
release = str(os.getenv("VERSION"))

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # This enables automodule
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",  # For Google-style docstrings
    "myst_parser",
    "pydantic",
]

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "special-members": "__init__",
}


# Don't skip __init__ method documentation
autoclass_content = "both"

templates_path = ["_templates"]
exclude_patterns = []

source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "markdown",
    ".md": "markdown",
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
theme_options = ThemeOptions(
    # Add your theme options. For example:
    show_breadcrumbs=True,
    logo_light="./llmfy-logo-circle.png",
    logo_dark="./llmfy-logo-circle.png",
    show_scrolltop=False,
)


# Select a color scheme for light mode
pygments_style = "emacs"
# Select a different color scheme for dark mode
pygments_style_dark = "monokai"
html_title = f"LLMFY v{release}"
html_short_title = f"LLMFY v{release}"
html_favicon = "./llmfy-logo-circle.png"
# html_logo = "./llmfy-logo-square.png"
html_theme_options = asdict(theme_options)
html_theme = "sphinxawesome_theme"
html_permalinks_icon = "<span></span>"
version = release
html_static_path = ["_static"]
