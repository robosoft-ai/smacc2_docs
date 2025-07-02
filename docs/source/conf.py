# Configuration file for the Sphinx documentation builder.

# -- Project information

project = 'SMACC2'
copyright = '2025, Robosoft Inc.'
author = 'Brett Aldrich'

release = '0.1'
version = '0.1.0'

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'

html_context = {
    "display_github": True,
    "github_user": "robosoft-ai",
    "github_repo": "smacc2_docs",
    "github_version": repos_file_branch + "/",
    "conf_py_path": "/docs/source/",
    "source_suffix": source_suffix,
    "favicon": "favicon_ros-controls.ico",
    "logo": "logo_ros-controls.png"
}

html_favicon = "images/favicon_ros-controls.ico"
html_logo = "images/logo_ros-controls.png"


github_url = "https://https://github.com/robosoft-ai/smacc2_docs"


# -- Options for EPUB output
epub_show_urls = 'footnote'
