# -*- coding: utf-8 -*-
"""

neoTaxonomy - A python API to deal with NCBI taxonomy in a neo4j database
Copyright (C) 2016-2017 Paolo Cozzi <paolo.cozzi@ptp.it>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


Created on Tue Nov 29 12:48:33 2016

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import io
import re

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    README = f.read()

with open(path.join(here, 'NEWS.txt'), encoding='utf-8') as f:
    NEWS = f.read()

# define function to parse versions
# https://packaging.python.org/en/latest/single_source_version.html
def read(*names, **kwargs):
    with io.open(
        path.join(path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ) as fp:
        return fp.read()

def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")
    
# package version
version = find_version('src/neotaxonomy', "__init__.py")

install_requires = [
    # List your project dependencies here.
    # For more details, see:
    # http://packages.python.org/distribute/setuptools.html#declaring-dependencies
    "py2neo",
]


setup(
    name='neotaxonomy',
    
    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=version,
    
    description="A neo4j API for NCBI taxonomy database",
    long_description=README + '\n\n' + NEWS,
    
    # The project's main homepage.
    url='',
    
    # Author details
    author='Paolo Cozzi',
    author_email='paolo.cozzi@ptp.it',
    
    # Provide the type of license you are using
    license='GPLv3',
    
    # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 1 - Planning",
        
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Topic :: Database :: Front-Ends",
        "Topic :: Education",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
        
        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        # TODO: add more python versions
    ],
    
    # List keywords that describe your project.
    keywords='NCBI taxonomy neo4j',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    # Use the exclude keyword argument to omit packages that are not intended 
    # to be released and installed    
    packages=find_packages('src', exclude=['contrib', 'docs', 'tests*']),
    package_dir = {'': 'src'},
    include_package_data=True,
    
    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=install_requires,

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
#    package_data={
#        'sample': ['package_data.dat'],
#    },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
#    data_files=[('my_data', ['data/data_file'])],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts':
            ['fillTaxonomyDB=neotaxonomy.command_line:fillTaxonomyDB',
             'taxaid2lineage=neotaxonomy.command_line:taxaid2lineage']
    },
)
