#!/usr/bin/env python

import glob
from setuptools import setup, find_packages
import codecs
import os
import re

here = os.path.abspath(os.path.dirname(__file__))

# Read the version number from a source file.
# Why read it, and not import?
# see https://groups.google.com/d/topic/pypa-dev/0PkjVpcxTzQ/discussion
def find_version(*file_paths):
    # Open in Latin-1 so that we avoid encoding errors.
    # Use codecs.open for Python 2 compatibility
    with codecs.open(os.path.join(here, *file_paths), 'r', 'latin1') as f:
        version_file = f.read()

    # The version line must have the form
    # __version__ = 'ver'
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


# Get the long description from the relevant file
with codecs.open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name = 'linsharecli',
    version=find_version('linsharecli', '__init__.py'),
    description = 'LinShare command line interface.',
    long_description=long_description,

    # The project URL.
    url = 'https://github.com/fred49/linshare-cli',

    # Author details
    author = 'Frederic MARTIN',
    author_email = 'frederic.martin.fma@gmail.com',

    # Choose your license
    license = "GPL3",

    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Environment :: Console',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],

    # What does your project relate to?
    #keywords='',

    test_suite='tests.get_all_tests',

    entry_points={
        'console_scripts': [
            'linshareadmcli=linsharecli.admin:CLI',
            'linshareadmcli-config=linsharecli.admin:generate_config',
            'linsharecli=linsharecli.user:CLI',
            'linsharecli-config=linsharecli.user:generate_config',
        ],
    },

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages.
    packages=find_packages(exclude=["contrib", "docs", "tests*"]),

    # List run-time dependencies here.  These will be installed by pip when your
    # project is installed.
    install_requires=[
        'argtoolbox>=1.1.4,<1.2.0',
        'linshareapi>=1.0.9,<1.1.0',
        'progressbar2',
        'veryprettytable==0.8.1',
        'humanfriendly',
        'mock==2.0.0',
    ],
)
