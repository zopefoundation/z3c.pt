##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Setup
"""
import os

from setuptools import find_packages
from setuptools import setup


def read(*filenames):
    with open(os.path.join(*filenames)) as f:
        return f.read()


setup(
    name="z3c.pt",
    version='4.5',
    author="Malthe Borch and the Zope Community",
    author_email="zope-dev@zope.dev",
    description="Fast ZPT engine.",
    long_description=(
        read("README.rst")
        + "\n\n"
        + read("src", "z3c", "pt", "README.rst")
        + "\n\n"
        + read("CHANGES.rst")
    ),
    license="ZPL",
    keywords="tal tales pagetemplate zope chameleon",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Topic :: Text Processing :: Markup :: HTML",
        "Topic :: Text Processing :: Markup :: XML",
        "Framework :: Zope :: 3",
    ],
    url="https://github.com/zopefoundation/z3c.pt",
    project_urls={
        'Sources': 'https://github.com/zopefoundation/z3c.pt',
        'Issue Tracker': 'https://github.com/zopefoundation/z3c.pt/issues',
    },
    namespace_packages=["z3c"],
    packages=find_packages("src"),
    package_dir={"": "src"},
    python_requires='>=3.9',
    install_requires=[
        "setuptools",
        "zope.interface",
        "zope.component",
        "zope.i18n >= 3.5",
        "zope.traversing",
        "zope.contentprovider",
        "Chameleon >= 2.4",
    ],
    extras_require={
        "test": [
            "zope.pagetemplate",
            "zope.testing",
            "zope.testrunner",
        ],
        "docs": [
            "Sphinx",
        ]
    },
    include_package_data=True,
    zip_safe=False,
)
