# Configuration file for the Sphinx documentation builder.

# -- Project information

project = 'SMACC2'
copyright = '2025, Robosoft Inc.'
author = 'Brett Aldrich'

release = '0.1'
version = 'State Machine Asynchronous C++'

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx_copybutton',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_css_files = ['custom.css']

html_favicon = '_static/SiteIcon-White.png'
html_show_sourcelink = False

# -- Options for EPUB output
epub_show_urls = 'footnote'
