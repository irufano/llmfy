from dataclasses import asdict
import os
import sys

from dotenv import load_dotenv
from sphinxawesome_theme import ThemeOptions

# sys.path.insert(0, os.path.abspath("../.."))
sys.path.insert(0, os.path.abspath("../.."))
load_dotenv()


# Auto-generate API documentation
def run_apidoc(app):
    """Generate API documentation"""
    ignore_paths = []

    argv = [
        "-f",  # Overwrite existing files
        "-o",
        "docs/source/",  # Output directory
        "../llmfy",  # Source directory
    ] + ignore_paths

    try:
        # Import here to avoid issues if sphinx-apidoc is not available
        from sphinx.ext.apidoc import main

        main(argv)
    except Exception as e:
        print(f"Running `sphinx-apidoc` failed!\n{e}")


def setup(app):
    app.connect("builder-inited", run_apidoc)


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
]

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
