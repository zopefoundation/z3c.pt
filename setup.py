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
from setuptools import setup, find_packages


def read(*filenames):
    with open(os.path.join(*filenames)) as f:
        return f.read()


setup(
    name="z3c.pt",
    version='3.3.1.dev0',
    author="Malthe Borch and the Zope Community",
    author_email="zope-dev@zope.org",
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
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
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
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*',
    install_requires=[
        "setuptools",
        "six",
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
