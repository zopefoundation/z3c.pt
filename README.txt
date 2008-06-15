Overview
--------

The z3c.pt package provides an alternative implementation of the TAL
template language including i18n. It also provides a simple text
template class that allows expression interpolation.

Casual benchmarks pegs it 11x more performant than ``zope.pagetemplate``.

In a nutshell:

* Templates are parsed and compiled into Python bytecode
* While rendering only Python code is executed and no parsing happens
* Pluggable expression implementation
* Support for expression interpolation using the ${<expression>}-format
* Non-XML friendly

Note: The METAL macro language is not supported.


Usage
-----

See README.txt inside package for general usage; to register the
default expression types, load the package component configuration
file (configure.zcml).


Template and expression language
--------------------------------

The template and expression language is based loosely on the TAL 1.4
specification*. Some notable changes:

1. Tuples are allowed in the tal:define statement:

      tal:define="(a, b, c) [1, 2, 3]"

2. Generators are allowed in tal:repeat statements. Note that the
   repeat variable is not available in this case.

      tal:repeat="i <some generator>"

3. Attribute-access to dictionary entries is allowed in
   Python-expressions, e.g.

      dictionary.key

   can be used instead of ``dictionary['key']``.

4. Expression interpolation is allowed in attributes and HTML content.

       <a href="mailto:${context.email}">${context.email}</a>

5. Default expression type can be set using ``tal:default-expression``.
   This is an alternative to providing the expression type before each
   expression.
   
.. _TAL: http://wiki.zope.org/ZPT/TALSpecification14


Development
-----------

If you want to use the code directly from trunk (recommended only for
development and testing usage), provide ``z3c.pt==dev`` as your
dependency.

http://svn.zope.org/z3c.pt/trunk#egg=z3c.pt-dev

