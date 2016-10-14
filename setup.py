#!/usr/bin/env python
import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup_args = {}
install_requires = ['param>=1.4.1', 'ipywidgets>=5.1.5']

setup_args.update(dict(
    name='paramnb',
    version="1.0.2",
    install_requires = install_requires,
    url = 'https://github.com/ioam/paramnb',
    description='Generate ipywidgets from Parameterized objects in the notebook',
    long_description=open('README.rst').read() if os.path.isfile('README.rst') else 'Consult README.rst',
    author= "IOAM",
    author_email= "holoviews@gmail.com",
    maintainer= "IOAM",
    maintainer_email= "holoviews@gmail.com",
    platforms=['Windows', 'Mac OS X', 'Linux'],
    packages = ["paramnb"],
    provides = ["paramnb"],
))


if __name__=="__main__":
    if ('upload' in sys.argv) or ('sdist' in sys.argv):
        import paramnb
        paramnb.__version__.verify(setup_args['version'])

    setup(**setup_args)
