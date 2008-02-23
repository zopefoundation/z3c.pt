Overview
--------
		      
The z3c.pt package provides an alternative implementation of the TAL
template language including i18n.

Casual benchmarks pegs it 12x more performant than ``zope.pagetemplate``.

In a nutshell:

  - Templates are bytecode-compiled
  - Only Python-expressions are supported
  - Depends only on lxml
  - Adds support for expression interpolation
  
The METAL macro language is not supported.

Template and expression language
--------------------------------

The template and expression language is based loosely on the TAL 1.4
specification*. Some notable changes:

1. Only Python-expressions are allowed. Expressions can have
   try-except fallbacks using the vertical bar syntax:

      tal:content="<expression> | <first fallback> | <second fallback> | ..."

2. Tuples are allowed in the tal:define statement:

      tal:define="(a, b, c) [1, 2, 3]"

3. Generators are allowed in tal:repeat statements. Note that the
   repeat variable is not available in this case.

      tal:repeat="i <some generator>"

4. Attribute-access to dictionary entries is allowed, e.g.

      dictionary.key

   can be used instead of ``dictionary['key']``.

5. Expressions that return a callable are called.

6. Expression interpolation is allowed:

       <a href="mailto:${context.email}">${context.email}</a>

7. Attribute-values are always escaped; document expressions are
   never.
   
*) http://wiki.zope.org/ZPT/TALSpecification14

Development
-----------

If you want to use the code directly from trunk, provide
``z3c.pt==dev`` as your dependency.

http://svn.zope.org/z3c.pt/trunk#egg=z3c.pt-dev
