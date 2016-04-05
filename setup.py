#!/usr/bin/env python
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup_args = {}

setup_args.update(dict(
    name='paramnb',
    version="0.0.1",
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
    setup(**setup_args)
