# -*- coding: utf-8 -*-

from nbsite.shared_conf import *

###################################################
# edit things below as appropriate for your project

project = u'ParamNB'
authors = u'ParamNB GitHub contributors'
copyright = u'2017 ' + authors
description = 'Automatically generate ipywidgets from Parameterized objects in a Jupyter notebook.'

import paramnb
version = release = str(paramnb.__version__)

html_static_path += ['_static']
html_theme = 'sphinx_ioam_theme'
# logo file etc should be in html_static_path, e.g. _static
html_theme_options = {
#    'custom_css':'bettercolors.css',
#    'logo':'amazinglogo.png',
#    'favicon':'amazingfavicon.ico'
}

_NAV =  (
)

html_context.update({
    'PROJECT': project,
    'DESCRIPTION': description,
    'AUTHOR': authors,
    # will work without this - for canonical (so can ignore when building locally or test deploying)    
    'WEBSITE_SERVER': 'https://ioam.github.io/paramnb',
    'VERSION': version,
    'NAV': _NAV,
    # by default, footer links are same as those in header
    'LINKS': _NAV,
    'SOCIAL': (
        ('Gitter', '//gitter.im/ioam/holoviews'),
        ('Twitter', '//twitter.com/holoviews'),
        ('Github', '//github.com/ioam/paramnb'),
    )
})
