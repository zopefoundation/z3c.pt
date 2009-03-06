.. _index:

======
z3c.pt
======

This package provides a fast implementation of the Zope Page Templates (ZPT) language which aims to be fully compatible with the reference implementation. The template engine is based on Chameleon.

.. note:: If you're looking to use Chameleon outside a Zope 2 or 3 environment, the `chameleon.zpt <http://pypi.python.org/pypi/chameleon.zpt>`_ package provides a light-weight implementation of the ZPT language.

Zope Page Templates (ZPT) is a system which can generate HTML and XML.
ZPT is formed by the *Template Attribute Language* (*TAL*), the
*Expression Syntax* (*TALES*), *Intertionalization*  (*I18N*) and the *Macro Expansion Template Attribute Language* (*METAL*).

The package also implementation a text-mode which supports non-structural content like JavaScript.

Language Reference
==================

For a general reference, see the `documentation <http://chameleon.repoze.org/docs/zpt>`_ for the :mod:`chameleon.zpt` package. In the present reference, the language details that are specific to this implementation are described.


.. toctree::
   :maxdepth: 2

   narr/tales
   narr/i18n

API documentation
=================

:mod:`z3c.pt` API documentation.

.. toctree::
   :maxdepth: 2

   api

Support and Development
=======================

This package is developed and maintained by `Malthe Borch <mailto:mborch@gmail.com>`_ and the Zope Community.

To report bugs, use the `bug tracker <https://bugs.launchpad.net/z3c.pt/>`_.

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

