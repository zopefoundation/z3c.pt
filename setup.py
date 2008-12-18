from setuptools import setup, find_packages
import sys
version = '1.0b6'

install_requires = [
    'setuptools',
    'zope.interface',
    'zope.component',
    'zope.i18n >= 3.5',
    'zope.traversing',
    'zope.contentprovider',
    'chameleon.core >= 1.0b14',
    'chameleon.zpt >= 1.0b8',
    ]

if sys.version_info[:3] < (2,5,0):
    install_requires.append('elementtree')

setup(name='z3c.pt',
      version=version,
      description="Python template compiler which supports the Genshi and "
                  "ZPT template languages including macro extensions and "
                  "internationalization.",
      long_description=open("README.txt").read() + open("CHANGES.txt").read(),
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Text Processing :: Markup :: HTML",
        "Topic :: Text Processing :: Markup :: XML",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='',
      author='Malthe Borch and the Zope Community',
      author_email='zope-dev@zope.org',
      url='',
      license='ZPL',
      namespace_packages=['z3c'],
      packages = find_packages('src'),
      package_dir = {'':'src'},
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      extras_require={'lxml':['lxml>=2.1.1']},
      )
