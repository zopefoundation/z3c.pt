.. _tales_chapter:

Template Attribute Language Expression Syntax (TALES)
=====================================================

The *Template Attribute Language Expression Syntax* (TALES) standard
describes expressions that supply :ref:`tal_chapter` and
:ref:`metal_chapter` with data.  TALES is *one* possible expression
syntax for these languages, but they are not bound to this definition.
Similarly, TALES could be used in a context having nothing to do with
TAL or METAL.

TALES expressions are described below with any delimiter or quote
markup from higher language layers removed.  Here is the basic
definition of TALES syntax::

      Expression  ::= [type_prefix ':'] String
      type_prefix ::= Name

Here are some simple examples::

      a.b.c
      path:a/b/c
      nothing
      path:nothing
      python: 1 + 2
      string:Hello, ${user/getUserName}

The optional *type prefix* determines the semantics and syntax of the
*expression string* that follows it.  A given implementation of TALES
can define any number of expression types, with whatever syntax you
like. It also determines which expression type is indicated by
omitting the prefix.

TALES Expression Types
----------------------

These are the TALES expression types supported by :mod:`z3c.pt`:

* ``python`` - execute a Python expression

* ``path`` - locate a value by its "path" (via getattr and getitem)

* ``nocall`` - locate an object by its path.

* ``not`` - negate an expression

* ``string`` - format a string

.. note:: if you do not specify a prefix within an expression context,
   :mod:`z3c.pt`` assumes that the expression is a *python*
   expression.

.. warning:: The reference implementation of ZPT has an expression type ``exists``.  :mod:`z3c.pt` has no such expression type.

.. _tales_built_in_names:

Built-in Names
--------------

These are the names always available to TALES expressions in
:mod:`z3c.pt`:

- ``nothing`` - special value used by to represent a *non-value*
  (Python ``None``).

- ``default`` - special value used to specify that existing text
   should not be replaced. See the documentation for individual TAL
   statements for details on how they interpret *default*.

- ``repeat`` - the *repeat* variables; see :ref:`tal_repeat` for more
  information.

- ``attrs`` - a dictionary containing the initial values of the
  attributes of the current statement tag.

``nocall`` expressions
----------------------

Syntax
~~~~~~

``nocall`` expression syntax::

        nocall_expression ::= 'nocall:' path_expression

Description
~~~~~~~~~~~

Nocall expressions avoid calling the __call__ method of the last
element of a path expression.

An ordinary path expression tries to render the object that it
fetches.  This means that if the object is a function, method, or some
other kind of executable thing, then expression will evaluate to the
result of calling the object.  This is usually what you want, but not
always.

Examples
~~~~~~~~

Using nocall to prevent calling the ``__call__`` of the last element
of a path expression::

        <span tal:define="doc nocall:context/acallabledocument"
              tal:content="string:${doc/getId}: ${doc/title}">
        Id: Title</span>

``not`` expressions
-------------------

Syntax
~~~~~~

``not`` expression syntax::

        not_expression ::= 'not:' expression

Description
~~~~~~~~~~~

A ``not`` expression evaluates the expression string (recursively) as
a full expression, and returns the boolean negation of its value. If
the expression supplied does not evaluate to a boolean value, *not*
will issue a warning and *coerce* the expression's value into a
boolean type based on the following rules:

#. the number 0 is *false*

#. positive and negative numbers are *true*

#. an empty string or other sequence is *false*

#. a non-empty string or other sequence is *true*

#. a *non-value* (e.g. None) is *false*

#. all other values are implementation-dependent.

If no expression string is supplied, an error should be generated.

:mod:`z3c.pt` considers all objects not specifically listed above as
*false* to be *true*.

Examples
~~~~~~~~

Testing a sequence::

        <p tal:condition="not:context.keys()">
          There are no keys.
        </p>

``path`` expressions
--------------------

Syntax
~~~~~~

Path expression syntax::

        PathExpr    ::= Path [ '|' Expression ]
        Path        ::= variable [ '/' PathSegment ]*
        variable    ::= Name
        PathSegment ::= ( '?' variable ) | PathChar+
        PathChar    ::= AlphaNumeric | ' ' | '_' | '-' | '.' | ',' | '~'

Description
~~~~~~~~~~~

A path expression consists of a *path* optionally followed by a
vertical bar (|) and alternate expression.  A path consists of one or
more non-empty strings separated by slashes. The first string must be
a variable name (a built-in variable or a user defined variable), and
the remaining strings, the *path segments*, may contain letters,
digits, spaces, and the punctuation characters underscore, dash,
period, comma, and tilde.

A limited amount of indirection is possible by using a variable name
prefixed with ``?`` as a path segment.  The variable must contain a
string, which replaces that segment before the path is traversed.

For example::

        request/cookies/oatmeal
        nothing
        here/some-file 2001_02.html.tar.gz/foo
        root/to/branch | default

        request/name | string:Anonymous Coward
        here/?tname/macros/?mname

When a path expression is evaluated, :mod:`z3c.pt` attempts to
traverse the path, from left to right, until it succeeds or runs out
of paths segments.  To traverse a path, it first fetches the object
stored in the variable.  For each path segment, it traverses from the
current object to the subobject named by the path segment. Subobjects
are located according to standard :mod:`z3c.pt` traversal rules

.. warning:: need to describe traversal rules here.  I'd suggest we
   make them pluggable and not require zope.traversal or
   zope.security.

Once a path has been successfully traversed, the resulting object is
the value of the expression.  If it is a callable object, such as a
method or template, it is called.

If a traversal step fails, and no alternate expression has been
specified, an error results.  Otherwise, the alternate expression is
evaluated.

The alternate expression can be any TALES expression. For example,
``path:request/name | string:Anonymous Coward`` is a valid path
expression.  This is useful chiefly for providing default values, such
as strings and numbers, which are not expressable as path expressions.
Since the alternate expression can be a path expression, it is
possible to "chain" path expressions, as in ``first | second | third |
nothing``.

If no path is given the result is *nothing*.

Since every path must start with a variable name, you need a set of
starting variables that you can use to find other objects and values.
See the :ref:`tales_built_in_names` for a list of built-in variables.
Variable names are looked up first in locals, then in the built-in
list, so the built-in variables act just like built-ins in Python;
They are always available, but they can be shadowed by a local
variable declaration.

Examples
~~~~~~~~

Inserting a cookie variable or a property::

        <span tal:replace="request/cookies/pref | here/pref">
          preference
        </span>

Inserting the user name::

        <p tal:content="user/getUserName">
          User name
        </p>

``python`` expressions
----------------------

Syntax
~~~~~~

Python expression syntax::

        Any valid Python language expression

Description
~~~~~~~~~~~

Python expressions evaluate Python code in a security-restricted
environment. Python expressions offer the same facilities as those
available in Python-based Scripts and DTML variable expressions.

.. warning: Security restrictions?

Built-in Functions
~~~~~~~~~~~~~~~~~~

You can use any name passed in to the ``render`` method of a template
within a Python expression.

These functions are also available in Python expressions:

``path(string)`` -- Evaluate a TALES path expression.

``string(string)`` -- Evaluate a TALES string expression.

``nocall(string)`` -- Evaluates a TALES nocall expression.

Examples
~~~~~~~~

Using a module usage (pick a random choice from a list)::

    <span tal:replace="random.choice(['one', 
                         'two', 'three', 'four', 'five'])">
      a random number between one and five
    </span>

String processing (capitalize the user name)::

    <p tal:content="user.getUserName().capitalize()">
      User Name
    </p>

Basic math (convert an image size to megabytes)::

    <p tal:content="image.getSize() / 1048576.0">
      12.2323
    </p>

String formatting (format a float to two decimal places)::

    <p tal:content="'%0.2f' % size">
      13.56
    </p>

``string`` expressions
----------------------

Syntax
~~~~~~

String expression syntax::

        string_expression ::= ( plain_string | [ varsub ] )*
        varsub            ::= ( '$' Path ) | ( '${' Path '}' )
        plain_string      ::= ( '$$' | non_dollar )*
        non_dollar        ::= any character except '$'

Description
~~~~~~~~~~~

String expressions interpret the expression string as text. If no
expression string is supplied the resulting string is *empty*. The
string can contain variable substitutions of the form ``$name`` or
``${path}``, where ``name`` is a variable name, and ``path`` is a path
expression.  The escaped string value of the path expression is
inserted into the string.

.. note:: To prevent a ``$`` from being interpreted this
   way, it must be escaped as ``$$``.

Examples
~~~~~~~~

Basic string formatting::

    <span tal:replace="string:$this and $that">
      Spam and Eggs
    </span>

Using paths::

    <p tal:content="string:${request/form/total}">
      total: 12
    </p>

Including a dollar sign::

    <p tal:content="string:$$$cost">
      cost: $42.00
    </p>

