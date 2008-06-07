from setuptools import setup, find_packages

version = '0.8.4'

setup(name='z3c.pt',
      version=version,
      description="An implementation of the TAL template language.",
      long_description=open("README.txt").read() + open("docs/HISTORY.txt").read(),
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Text Processing :: Markup :: HTML",
        "Topic :: Text Processing :: Markup :: XML",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='',
      author='Malthe Borch',
      author_email='mborch@gmail.com',
      url='',
      license='ZPL',
      namespace_packages=['z3c'],
      packages = find_packages('src'),
      package_dir = {'':'src'},
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'lxml',
          'zope.interface',
          'zope.component',
          'zope.i18n',
          'zope.traversing',
          'zope.security',
      ],
      )
