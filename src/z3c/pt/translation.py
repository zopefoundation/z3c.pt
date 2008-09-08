from StringIO import StringIO

import generation
import codegen
import clauses
import doctypes
import itertools
import types
import utils
import config
import etree
import marshal
import htmlentitydefs

class Node(object):
    """Element translation class.

    This class implements the translation node for an element in the
    template document tree.

    It's used internally by the translation machinery.
    """

    symbols = config.SYMBOLS
    
    def __init__(self, element):
        self.element = element

    @property
    def stream(self):
        return self.element.stream
    
    def update(self):
        self.element.update()
    
    def begin(self):
        self.stream.scope.append(set())
        self.stream.begin(self.serialize())
        
    def end(self):
        self.stream.end(self.serialize())
        self.stream.scope.pop()

    def body(self):
        if not self.skip:
            for element in self.element:
                element.node.update()

            for element in self.element:
                element.node.visit()
                    
    def visit(self):
        assert self.stream is not None, "Must use ``start`` method."

        for element in self.element:
            if not isinstance(element, Element):
                self.wrap_literal(element)

        self.update()
        self.begin()
        self.body()
        self.end()

    def serialize(self):
        """Serialize element into clause-statements."""

        _ = []

        # i18n domain
        if self.translation_domain is not None:
            _.append(clauses.Define(
                self.symbols.domain, types.value(repr(self.translation_domain))))

        # variable definitions
        if self.define is not None:
            for declaration, expression in self.define:
                if declaration.global_scope:
                    _.append(clauses.Define(
                        declaration, expression, self.symbols.scope))
                else:
                    _.append(clauses.Define(declaration, expression))

        # macro method
        macro = self.macro
        if macro is not None:
            _.append(clauses.Method(
                macro.name, macro.args))
                
        # tag tail (deferred)
        tail = self.element.tail
        if tail and not self.fill_slot:
            if isinstance(tail, unicode):
                tail = tail.encode('utf-8')
            _.append(clauses.Out(tail, defer=True))

        # condition
        if self.condition is not None:
            _.append(clauses.Condition(self.condition))

        # repeat
        if self.repeat is not None:
            variables, expression = self.repeat
            if len(variables) != 1:
                raise ValueError(
                    "Cannot unpack more than one variable in a "
                    "repeat statement.")
            _.append(clauses.Repeat(variables[0], expression))

        content = self.content

        # macro slot definition
        if self.define_slot:
            # check if slot has been filled
            variable = self.symbols.slot + self.define_slot
            if variable in itertools.chain(*self.stream.scope):
                content = types.value(variable)

        # set dynamic content flag
        dynamic = content or self.translate is not None

        # static attributes are at the bottom of the food chain
        attributes = utils.odict()
        attributes.update(self.static_attributes)

        # dynamic attributes
        dynamic_attrs = self.dynamic_attributes or ()
        dynamic_attr_names = []
        
        for variables, expression in dynamic_attrs:
            if len(variables) != 1:
                raise ValueError("Tuple definitions in assignment clause "
                                     "is not supported.")

            variable = variables[0]
            attributes[variable] = expression
            dynamic_attr_names.append(variable)

        # translated attributes
        translated_attributes = self.translated_attributes or ()
        for variable, msgid in translated_attributes:
            if msgid:
                if variable in dynamic_attr_names:
                    raise ValueError(
                        "Message id not allowed in conjunction with "
                        "a dynamic attribute.")

                value = types.value('"%s"' % msgid)

                if variable in attributes:
                    default = '"%s"' % attributes[variable]
                    expression = self.translate_expression(value, default=default)
                else:
                    expression = self.translate_expression(value)
            else:
                if variable in dynamic_attr_names or variable in attributes:
                    text = '"%s"' % attributes[variable]
                    expression = self.translate_expression(text)
                else:
                    raise ValueError("Must be either static or dynamic "
                                     "attribute when no message id "
                                     "is supplied.")

            attributes[variable] = expression

        # tag
        text = self.element.text
        if self.omit is not True:
            selfclosing = text is None and not dynamic and len(self.element) == 0
            tag = clauses.Tag(
                self.element.tag, attributes,
                expression=self.dict_attributes, selfclosing=selfclosing,
                cdata=self.cdata is not None)
            if self.omit:
                _.append(clauses.Condition(
                    types.value("not (%s)" % self.omit), [tag], finalize=False))
            else:
                _.append(tag)

        # tag text (if we're not replacing tag body)
        if text and not dynamic:
            if isinstance(text, unicode):
                text = text.encode('utf-8')
            _.append(clauses.Out(text))

        # dynamic content
        if content:
            msgid = self.translate
            if msgid is not None:
                if msgid:
                    raise ValueError(
                        "Can't use message id with dynamic content translation.")

                _.append(clauses.Assign(content, self.symbols.tmp))
                content = self.translate_expression(
                    types.value(self.symbols.tmp))
                
            _.append(clauses.Write(content))

        # include
        elif self.include:
            # compute macro function arguments and create argument string
            arguments = ", ".join(
                ("%s=%s" % (arg, arg) for arg in \
                 itertools.chain(*self.stream.scope)))

            # XInclude's are similar to METAL macros, except the macro
            # is always defined as the entire template.

            # first we compute the filename expression and write it to
            # an internal variable
            _.append(clauses.Assign(self.include, self.symbols.include))

            # call template
            _.append(clauses.Write(
                types.template(
                "%%(xincludes)s.get(%%(include)s, %s).render(macro='', %s)" % \
                (repr(self.format), arguments))))
            
        # use macro
        elif self.use_macro:
            # for each fill-slot element, create a new output stream
            # and save value in a temporary variable
            kwargs = []
            for element in self.element.xpath(
                './/*[@metal:fill-slot]', namespaces={'metal': config.METAL_NS}):
                if element.node.fill_slot is None:
                    # XXX this should not be necessary, but the above
                    # xpath expression finds non-"metal:fill-slot"
                    # nodes somehow on my system; this is perhaps due
                    # to a bug in the libxml2 version I'm using; we
                    # work around it by just skipping the element.
                    # (chrism)
                    continue

                variable = self.symbols.slot+element.node.fill_slot
                kwargs.append((variable, variable))
                
                subclauses = []
                subclauses.append(clauses.Define(
                    types.declaration((self.symbols.out, self.symbols.write)),
                    types.template('%(init)s.initialize_stream()')))
                subclauses.append(clauses.Visit(element.node))
                subclauses.append(clauses.Assign(
                    types.template('%(out)s.getvalue()'), variable))
                _.append(clauses.Group(subclauses))
                
            _.append(clauses.Assign(self.use_macro, self.symbols.metal))

            # compute macro function arguments and create argument string
            if 'xmlns' in self.element.attrib:
                kwargs.append(('include_ns_attribute', repr(True)))
                
            arguments = ", ".join(
                tuple("%s=%s" % (arg, arg) for arg in \
                      itertools.chain(*self.stream.scope))+
                tuple("%s=%s" % kwarg for kwarg in kwargs))
                
            _.append(clauses.Write(
                types.value("%s(%s)" % (self.symbols.metal, arguments))))

        # translate body
        elif self.translate is not None:
            msgid = self.translate
            if not msgid:
                msgid = self.create_msgid()

            # for each named block, create a new output stream
            # and use the value in the translation mapping dict
            elements = [e for e in self.element if e.node.translation_name]

            if elements:
                mapping = self.symbols.mapping
                _.append(clauses.Assign(types.value('{}'), mapping))
            else:
                mapping = 'None'

            for element in elements:
                name = element.node.translation_name

                subclauses = []
                subclauses.append(clauses.Define(
                    types.declaration((self.symbols.out, self.symbols.write)),
                    types.template('%(init)s.initialize_stream()')))
                subclauses.append(clauses.Visit(element.node))
                subclauses.append(clauses.Assign(
                    types.template('%(out)s.getvalue()'),
                    "%s['%s']" % (mapping, name)))

                _.append(clauses.Group(subclauses))

            _.append(clauses.Assign(
                self.translate_expression(
                types.value(repr(msgid)), mapping=mapping,
                default=self.symbols.marker), self.symbols.result))

            # write translation to output if successful, otherwise
            # fallback to default rendition; 
            result = types.value(self.symbols.result)
            result.symbol_mapping[self.symbols.marker] = generation.marker
            condition = types.template('%(result)s is not %(marker)s')
            _.append(clauses.Condition(condition,
                        [clauses.UnicodeWrite(result)]))

            subclauses = []
            if self.element.text:
                subclauses.append(clauses.Out(self.element.text.encode('utf-8')))
            for element in self.element:
                name = element.node.translation_name
                if name:
                    value = types.value("%s['%s']" % (mapping, name))
                    subclauses.append(clauses.Write(value))
                else:
                    subclauses.append(clauses.Out(element.tostring()))
            if subclauses:
                _.append(clauses.Else(subclauses))

        return _

    def wrap_literal(self, element):
        index = self.element.index(element)

        t = self.element.makeelement(utils.meta_attr('literal'))
        t.attrib[utils.meta_attr('omit-tag')] = ''
        t.tail = element.tail
        t.text = unicode(element)
        for child in element.getchildren():
            t.append(child)
        self.element.remove(element)
        self.element.insert(index, t)
        t.update()

    def create_msgid(self):
        """Create an i18n msgid from the tag contents."""

        out = StringIO(self.element.text)
        for element in self.element:
            name = element.node.translation_name
            if name:
                out.write("${%s}" % name)
                out.write(element.tail)
            else:
                out.write(element.tostring())

        msgid = out.getvalue().strip()
        msgid = msgid.replace('  ', ' ').replace('\n', '')
        
        return msgid

    def translate_expression(self, value, mapping=None, default=None):
        format = "%%(translate)s(%s, domain=%%(domain)s, mapping=%s, " \
                 "target_language=%%(language)s, default=%s)"
        template = types.template(
            format % (value, mapping, default))

        # add translate-method to symbol mapping
        translate = generation.fast_translate
        template.symbol_mapping[config.SYMBOLS.translate] = translate

        return template
    
class Element(etree.ElementBase):
    """Template element class.

    To start translation at this element, use the ``start`` method,
    providing a code stream object.
    """

    node = property(Node)
    
    def start(self, stream):
        self._stream = stream
        self.node.visit()

    @property
    def stream(self):
        while self is not None:
            try:
                return self._stream
            except AttributeError:
                self = self.getparent()

        raise ValueError("Can't locate stream object.")

    meta_cdata = utils.attribute(
        utils.meta_attr('cdata'))
    
    meta_omit = utils.attribute(
        utils.meta_attr('omit-tag'))

    meta_attributes =  utils.attribute(
        utils.meta_attr('attributes'), lambda p: p.definitions)

    meta_replace = utils.attribute(
        utils.meta_attr('replace'), lambda p: p.output)

class VariableInterpolation:
    def update(self):
        translator = self.translator
        
        if self.text is not None:
            while self.text:
                text = self.text
                m = translator.interpolate(text)
                if m is None:
                    break

                t = self.makeelement(utils.meta_attr('interpolation'))
                expression = "structure " + \
                             (m.group('expression') or m.group('variable'))
                t.attrib[utils.meta_attr('replace')] = expression
                t.tail = text[m.end():]
                self.insert(0, t)
                t.update()

                if m.start() == 0:
                    self.text = text[2-len(m.group('prefix')):m.start()+1]
                else:
                    self.text = text[:m.start()+1]

        if self.tail is not None:
            while self.tail:
                m = translator.interpolate(self.tail)
                if m is None:
                    break

                t = self.makeelement(utils.meta_attr('interpolation'))
                expression = "structure " + \
                             (m.group('expression') or m.group('variable'))
                t.attrib[utils.meta_attr('replace')] = expression
                t.tail = self.tail[m.end():]
                parent = self.getparent()
                parent.insert(parent.index(self)+1, t)
                t.update()
                                
                self.tail = self.tail[:m.start()+len(m.group('prefix'))-1]

        for name in utils.get_attributes_from_namespace(self, config.XHTML_NS):
            value = self.attrib[name]

            if translator.interpolate(value):
                del self.attrib[name]

                attributes = utils.meta_attr('attributes')
                expr = '%s string:%s' % (name, value)
                if attributes in self.attrib:
                    self.attrib[attributes] += '; %s' % expr
                else:
                    self.attrib[attributes] = expr

class Compiler(object):
    """Template compiler. ``implicit_doctype`` will be used as the
    document type if the template does not define one
    itself. ``explicit_doctype`` may be used to explicitly set a
    doctype regardless of what the template defines."""

    doctype = None
    implicit_doctype = None
    
    def __init__(self, body, parser, implicit_doctype=None, explicit_doctype=None):
        # if no doctype is defined, prepend the implicit doctype to
        # the document source
        no_doctype_declaration = '<!DOCTYPE' not in body
        if implicit_doctype and no_doctype_declaration:
            # munge entities into declaration
            entities = "".join((
                '<!ENTITY %s "&#%s;">' % (name, text) for (name, text) in \
                htmlentitydefs.name2codepoint.items()))
            implicit_doctype = implicit_doctype[:-1] + '  [ %s ]>' % entities

            # prepend to body
            body = implicit_doctype + "\n" + body
            self.implicit_doctype = implicit_doctype
        
        self.root, parsed_doctype = parser.parse(body)

        if explicit_doctype is not None:
            self.doctype = explicit_doctype
        elif parsed_doctype and not no_doctype_declaration:
            self.doctype = parsed_doctype
            
        self.parser = parser

    @classmethod
    def from_text(cls, body, parser, implicit_doctype=None, explicit_doctype=None):
        compiler = Compiler(
            "<html xmlns='%s'></html>" % config.XHTML_NS, parser,
            implicit_doctype, explicit_doctype)
        compiler.root.text = body
        compiler.root.attrib[utils.meta_attr('omit-tag')] = ""
        return compiler

    def __call__(self, macro=None, params=()):
        if not isinstance(self.root, Element):
            raise ValueError(
                "Must define valid namespace for tag: '%s.'" % self.root.tag)

        # if macro is non-trivial, start compilation at the element
        # where the macro is defined
        if macro:
            elements = self.root.xpath(
                'descendant-or-self::*[@metal:define-macro="%s"]' % macro,
                namespaces={'metal': config.METAL_NS})

            if not elements:
                raise ValueError("Macro not found: %s." % macro)

            self.root = elements[0]
            del self.root.attrib[utils.metal_attr('define-macro')]

        if macro is None or 'include_ns_attribute' in params:
            # add namespace attribute
            namespace = self.root.tag.split('}')[0][1:]
            self.root.attrib['xmlns'] = namespace
        
        # choose function wrapper; note that if macro is the empty
        # string, we'll still use the macro wrapper
        if macro is not None:
            wrapper = generation.macro_wrapper
        else:
            wrapper = generation.template_wrapper

        # initialize code stream object
        stream = generation.CodeIO(
            self.root.node.symbols, indentation=1, indentation_string="\t")

        # initialize variable scope
        stream.scope.append(set(
            (stream.symbols.out, stream.symbols.write, stream.symbols.scope) + \
            tuple(params)))

        # output doctype if any
        if self.doctype and isinstance(self.doctype, (str, unicode)):
            doctype = (self.doctype +'\n').encode('utf-8')
            out = clauses.Out(doctype)
            stream.scope.append(set())
            stream.begin([out])
            stream.end([out])
            stream.scope.pop()

        # start generation
        self.root.start(stream)
        body = stream.getvalue()

        # prepare args
        ignore = 'target_language',
        args = ', '.join((param for param in params if param not in ignore))
        if args:
            args += ', '

        # prepare kwargs
        kwargs = ', '.join("%s=None" % param for param in params)
        if kwargs:
            kwargs += ', '

        # prepare selectors
        extra = ''
        for selector in stream.selectors:
            extra += '%s=None, ' % selector

        # wrap generated Python-code in function definition
        mapping = dict(
            args=args, kwargs=kwargs, extra=extra, body=body)
        mapping.update(stream.symbols.__dict__)
        source = wrapper % mapping
        
        # set symbol mappings as globals
        _globals = stream.symbol_mapping
        
        # compile code
        suite = codegen.Suite(source, globals=_globals)
        suite._globals.update(_globals)
        
        # execute code
        _locals = {}
        exec suite.code in suite._globals, _locals
        render = _locals['render']

        # remove namespace declaration
        if 'xmlns' in self.root.attrib:
            del self.root.attrib['xmlns']
        
        return ByteCodeTemplate(render, stream, self)

class ByteCodeTemplate(object):
    """Template compiled to byte-code."""

    def __init__(self, func, stream, compiler):
        self.func = func
        self.stream = stream
        self.compiler = compiler

    def __reduce__(self):
        reconstructor, (cls, base, state), kwargs = \
                       GhostedByteCodeTemplate(self).__reduce__()
        return reconstructor, (ByteCodeTemplate, base, state), kwargs

    def __setstate__(self, state):
        self.__dict__.update(GhostedByteCodeTemplate.rebuild(state))

    def render(self, *args, **kwargs):
        return self.func(generation, *args, **kwargs)
    
    @property
    def source(self):
        return self.stream.getvalue()
    
    @property
    def selectors(self):
        selectors = getattr(self, '_selectors', None)
        if selectors is not None:
            return selectors

        self._selectors = selectors = {}
        for element in self.compiler.root.xpath(
            './/*[@meta:select]', namespaces={'meta': config.META_NS}):
            name = element.attrib[utils.meta_attr('select')]
            selectors[name] = element.xpath

        return selectors

class GhostedByteCodeTemplate(object):
    suite = codegen.Suite("def render(): pass")
    
    def __init__(self, template):
        self.code = marshal.dumps(template.func.func_code)
        self.defaults = len(template.func.func_defaults or ())
        self.stream = template.stream

        compiler = template.compiler
        xmldoc = compiler.root.tostring()        
        if compiler.implicit_doctype is not None:
            xmldoc = compiler.implicit_doctype + "\n" + xmldoc
            
        self.parser = compiler.parser
        self.xmldoc = xmldoc
        
    @classmethod
    def rebuild(cls, state):
        _locals = {}
        exec cls.suite.code in cls.suite._globals, _locals
        func = _locals['render']
        func.func_defaults = ((None,)*state['defaults']) or None
        func.func_code = marshal.loads(state['code'])
        parser = state['parser']
        root, doctype = state['parser'].parse(state['xmldoc'])
        stream = state['stream']
        return dict(
            func=func,
            parser=parser,
            root=root,
            stream=stream)
            
