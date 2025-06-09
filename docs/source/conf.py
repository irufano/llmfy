from dataclasses import asdict
import os
import sys

from dotenv import load_dotenv
from sphinxawesome_theme import ThemeOptions

load_dotenv()
# sys.path.insert(0, os.path.abspath("../.."))
# Get the directory containing conf.py
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add your project to the path - adjust this based on your structure
# If llmfy is at the repo root: ../../llmfy
# If llmfy is in src/: ../../src/llmfy
project_root = os.path.join(current_dir, "..", "..")
llmfy_path = os.path.join(project_root, "llmfy")
sys.path.insert(0, project_root)


def run_apidoc(_):
    """Generate API documentation using sphinx-apidoc"""
    from sphinx.ext import apidoc

    # Check if the source directory exists
    if not os.path.exists(llmfy_path):
        print(f"Warning: Source directory {llmfy_path} does not exist")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Files in project root: {os.listdir(project_root)}")
        return

    # Arguments for sphinx-apidoc
    argv = [
        "--force",  # Overwrite existing files
        "--output-dir",
        current_dir,  # Output to docs/source/
        llmfy_path,  # Source directory to document
        "--separate",  # Put each module on its own page
    ]

    try:
        apidoc.main(argv)
        print("=== Generated .rst files ===")
        for f in os.listdir(current_dir):
            if f.endswith(".rst"):
                print(f"Generated: {f}")
        print(f"API documentation generated successfully from {llmfy_path}")
    except Exception as e:
        print(f"Error generating API docs: {e}")


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
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
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
