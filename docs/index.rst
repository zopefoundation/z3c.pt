.. _index:

======
z3c.pt
======

Python template compiler which supports the `Genshi
<http://genshi.edgewall.org/wiki/Documentation/xml-templates.html>`_
and `ZPT <http://wiki.zope.org/ZPT/TAL>`_ template language syntaxes
including macro extensions and i18n internationalization.

The compiler is developed by Malthe Borch and other contributors as
part of the `Zope <http://zope.org>`_ project.  It is written and
distributed under the `ZPL license
<http://www.zope.org/Resources/ZPL>`_.

Zope Page Templates (ZPT) is a system which can generate HTML and XML.
ZPT is formed by the *Template Attribute Language* (*TAL*) and the
*TAL Expression Syntax* (*TALES*), and the *Macro Expansion Template
Attribute Language* (*METAL*).

Genshi provides an XML-based template language that is heavily inspired
by `Kid <http://kid-templating.org/>`_, which in turn was inspired by
a number of existing template languages, namely XSLT, TAL, and PHP.

:mod:`z3c.pt` provides support for both ZPT and Genshi syntax.

TAL Support Documentation
=========================

Documentation related to TAL support in :mod:`z3c.pt`.

.. toctree::
   :maxdepth: 2

   narr/refimpls
   narr/tal
   narr/tales
   narr/metal
   narr/i18n

Genshi Support Documentation
============================

Documentation related to Genshi support in :mod:`z3c.pt`.

.. warning:: Need Genshi-related documentation.

API documentation
=================

:mod:`z3c.pt` API documentation.

.. toctree::
   :maxdepth: 2

   api

Support and Development
=======================

To report bugs, use the `bug tracker <http://code.google.com/p/z3c-pt>`_.

If you've got questions that aren't answered by this documentation,
please contact the `maillist
<http://groups.google.com/group/z3c_pt>`_.

Browse and check out tagged and trunk versions of :mod:`z3c.pt`
via the `Subversion repository <http://svn.zope.org/z3c.pt/>`_.  To
check out the trunk via Subversion, use this command::

  svn co svn://svn.zope.org/repos/main/z3c.pt/trunk z3c.pt

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

