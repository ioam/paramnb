#!/usr/bin/env python
import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup_args = {}
install_requires = ['param>=1.4.0']

setup_args.update(dict(
    name='paramnb',
    version="1.0.0",
    install_requires = install_requires,
    description='Generate ipywidgets from Parameterized objects in the notebook',
    long_description=open('README.rst').read() if os.path.isfile('README.rst') else 'Consult README.rst',
    author= "philippjfr",
    author_email= "philippjfr@continuum.io",
    maintainer= "philippjfr",
    maintainer_email= "philippjfr@continuum.io",
    platforms=['Windows', 'Mac OS X', 'Linux'],
    packages = ["paramnb"],
    provides = ["paramnb"],
))


if __name__=="__main__":
    if ('upload' in sys.argv) or ('sdist' in sys.argv):
        import param
        param.__version__.verify(setup_args['version'])

    setup(**setup_args)
