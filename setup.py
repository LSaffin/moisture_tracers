#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

requirements = [
    "docopt",
]

test_requirements = [

]

setup(
    author="Leo Saffin",
    author_email='l.saffin@leeds.ac.uk',
    python_requires='>=3',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',        
    ],
    description="Scripts for working with output from UM simulations with moisture tracers",
    install_requires=requirements,
    license="MIT license",
    include_package_data=True,
    keywords='moisture_tracers',
    name='moisture_tracers',
    packages=find_packages(include=['moisture_tracers', 'moisture_tracers.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/LSaffin/moisture_tracers',
    version='0.1.0',
    zip_safe=False,
)
