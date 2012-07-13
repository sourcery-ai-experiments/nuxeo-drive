#! /usr/bin/env python
#
# Copyright (C) 2012 Nuxeo
#

import sys

try:
    from cx_Freeze import setup, Executable

    base = None
    if sys.platform == "win32":
        #base = "Win32GUI"
        base = None
    executables = [Executable("bin/ndrive", base=base)]
    scripts = []
    # TODO: investigate with esky to get an auto-updateable version but
	# then make sure that we can still have .msi and .dmg packages
	# instead of simple zip files.
except ImportError:
    print("WARN: Install cx_Freeze if you want to build the "
          " standalone distribution of nxdrive.")
    from distutils.core import setup
    executables = []
    scripts = ["bin/ndrive"]

setup(
    name='nuxeo-drive',
    version='0.1.0',
    description="Desktop synchronization client for Nuxeo.",
    author="Olivier Grisel",
    author_email="ogrisel@nuxeo.com",
    url='http://github.com/nuxeo/nuxeo-drive',
    packages=[
        'nxdrive',
        'nxdrive.tests',
    ],
    scripts=scripts,
	executables=executables,
	options = {
        "build_exe": {
            "packages": [
                "sqlalchemy.dialects.sqlite",
                "nose",
            ],
            "excludes": ["ipdb", "clf", "IronPython"],
        },
	},
    long_description=open('README.rst').read(),
)
