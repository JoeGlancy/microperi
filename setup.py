#!/usr/bin/env python3
from setuptools import setup

with open('README.rst') as f:
    readme = f.read()

with open('AUTHORS') as f:
    authors = f.read().strip().replace('\n', ', ')

setup(
    name='MicroPeri',
    version='0.1.0',
    description='MicroPeri is a library for using the BBC micro:bit with MicroPython as an external peripheral device or sensor, using an API which closely replicates the micro:bit\'s MicroPython API.',
    long_description=readme,
    author=authors,
    author_email='',
    url='https://github.com/c0d3st0rm/microperi',
    scripts = [],
    license='mit',
    install_requires=[],
    package_data={'': ['README.rst',]},
)
