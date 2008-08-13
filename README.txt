Overview
--------

The z3c.pt package provides a fast template engine that supports the
following dialects of the attribute template language:

* Zope TAL
* Zope METAL
* Zope i18n
* Genshi

Non-structural documents are supported through Genshi's variable
interpolation syntax which is also available for XML templates.

Casual benchmarks pegs it 16x more performant than the reference
implementations for Zope TAL and Genshi.

In a nutshell:

* Templates are serialized and compiled into Python bytecode
* Pluggable expression implementation


Usage
-----

See README.txt inside package for general usage; to register the
default expression types, load the package component configuration
file (configure.zcml).


Compiler notes
--------------

The compiler is largely compatible with the targeted dialects. The TAL
implementation is based on the 1.4 language specification* while the
Genshi implementation is based on the documents for the 0.5 release**.

Some notable changes:

1. Tuple unpacking is allowed when defining variables:

      tal:define="(a, b, c) [1, 2, 3]"

2. Generators are allowed in tal:repeat statements. Note that the
   repeat variable is not available in this case.

      tal:repeat="i <some generator>"

3. Attribute-access to dictionary entries is allowed in
   Python-expressions, e.g.

      dictionary.key

   can be used instead of ``dictionary['key']``.

4. Default expression type can be set using ``tal:default-expression``.
   This is an alternative to providing the expression type before each
   expression.

5. The XPath select function provided to py:match-elements uses lxml
   and requires the use of the default namespace prefix "xmlns".

.. _TAL: http://wiki.zope.org/ZPT/TALSpecification14
.. _Genshi: http://genshi.edgewall.org/wiki/Documentation/xml-templates.html


Development
-----------

If you want to use the code directly from trunk (recommended only for
development and testing usage), provide ``z3c.pt==dev`` as your
dependency.

svn://svn.zope.org/repos/main/z3c.pt/trunk#egg=z3c.pt-dev

Want to contribute? Join #zope3-dev on Freenode IRC.

