.. _reflimpl_chapter:

Relationships to Reference Implementations
==========================================

:mod:`zc3.pt` implements both TAL and Genshi syntax.

The :mod:`z3c.pt` compiler is largely compatible with the targeted
dialects. The TAL implementation is based on the `1.4 language
specification <http://wiki.zope.org/ZPT/TALSpecification14>`_ while
the Genshi implementation is based on the documents for the `0.5
release <http://genshi.edgewall.org/wiki/Documentation/xml-templates.html>`_.

Notable Differences from TAL 1.4
--------------------------------

#. Tuple unpacking is allowed when using ``tal:define`` to define
   variables:

      ``tal:define="(a, b, c) [1, 2, 3]"``

#. Generators are allowed in ``tal:repeat`` statements. Note that the
   repeat variable is not available in this case

      ``tal:repeat="i <some generator>"``

#. Attribute-access to dictionary entries is allowed in
   Python-expressions, e.g.

      ``dictionary.key``

   can be used instead of ``dictionary['key']``.

#. The default expression type for a template can be set using the
   ``tal:default-expression`` attribute on an element.  This is an
   alternative to providing the expression type before each
   expression.

#. The ``global`` modifier for ``tal:define`` is not implemented.

#. The ``tal:on-error`` statement is not implemented.

Notable Differences from Genshi 0.5
-----------------------------------

#. The XPath select function provided to py:match-elements requires
   lxml and requires the use of the default namespace prefix "xmlns".

