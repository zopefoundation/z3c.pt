from setuptools import setup, find_packages

version = '0.3.3'

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
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['z3c'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'lxml<=1.3.6',
          'zope.i18n',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
