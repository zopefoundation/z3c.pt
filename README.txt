Overview
--------

The z3c.pt package provides an alternative implementation of the TAL
template language.

In a nutshell:

  - Templates are JIT-compiled
  - Only Python-expressions are supported
  - Depends only on lxml

The METAL macro language is not supported; i18n is on the to-do.

Template language
-----------------

The template language is based loosely on the TAL 1.4 specification
found here:

  * http://wiki.zope.org/ZPT/TALSpecification14
  
1. Only Python-expressions are allowed. Expressions can have
   try-except fallbacks using the vertical bar syntax:

      tal:content="<expression> | <first fallback> | <second fallback> | ..."

2. Tuples are allowed in the tal:define statement:

      tal:define="(a, b, c) [1, 2, 3]"

3. Generators are allowed in tal:repeat statements. Note that the
   repeat variable is not available in this case.

      tal:repeat="i <some generator>"
