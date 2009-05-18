from setuptools import setup, find_packages

version = '0.1'

setup(name='benchmark',
      version=version,
      description="Benchmark-suite for z3c.pt.",
      long_description="""\
      """,
      keywords='',
      author='Malthe Borch',
      author_email='mborch@gmail.com',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
         'zope.pagetemplate',
         'zope.tales',
         'z3c.pt',
         'lxml',
      ],
      )
