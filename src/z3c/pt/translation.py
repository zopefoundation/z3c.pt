from zope import component

from StringIO import StringIO

import generation
import clauses
import interfaces
import expressions
import itertools
import types
import utils
import config
import etree

class Element(etree.ElementBase):
    """Base compiler element class.

    This class represents an element in the template document tree. To
    start compilation at this node, use the ``start`` method,
    providing a code stream object.
    """

    symbols = config.SYMBOLS

    def start(self, stream):
        self._stream = stream
        self.visit()

    def update(self):
        pass
    
    def begin(self):
        self.stream.scope.append(set())
        self.stream.begin(self._serialize())
        
    def end(self):
        self.stream.end(self._serialize())
        self.stream.scope.pop()

    def body(self):
        if not self.node.skip:
            for element in self:
                element.update()

            for element in self:
                element.visit()
                    
    def visit(self, skip_macro=True):
        assert self.stream is not None, "Must use ``start`` method."

        if skip_macro and (self.node.method or self.node.define_macro):
            return

        for element in self:
            if not isinstance(element, Element):
                self._wrap_literal(element)

        self.update()
        self.begin()
        self.body()
        self.end()

    @property
    def stream(self):
        while self is not None:
            try:
                return self._stream
            except AttributeError:
                self = self.getparent()

        raise ValueError("Can't locate stream object.")
        
                    
    def _serialize(self):
        """Serialize element into clause-statements."""

        _ = []

        # i18n domain
        if self.node.translation_domain is not None:
            _.append(clauses.Define(
                self.symbols.domain, types.value(repr(self.node.translation_domain))))

        # variable definitions
        if self.node.define is not None:
            for declaration, expression in self.node.define:
                if declaration.global_scope:
                    _.append(clauses.Define(
                        declaration, expression, self.symbols.scope))
                else:
                    _.append(clauses.Define(declaration, expression))

        # macro method
        for element in tuple(self):
            if not isinstance(element, Element):
                continue

            macro = element.node.method
            if macro is not None:
                # define macro
                subclauses = []
                subclauses.append(clauses.Method(
                    self.symbols.macro, macro.args))
                subclauses.append(clauses.Visit(element))
                _.append(clauses.Group(subclauses))
                
                # assign to variable
                _.append(clauses.Define(
                    macro.name, types.parts((types.value(self.symbols.macro),))))

        # tag tail (deferred)
        tail = self.tail
        if tail and not self.node.fill_slot:
            if isinstance(tail, unicode):
                tail = tail.encode('utf-8')
            _.append(clauses.Out(tail, defer=True))

        # condition
        if self.node.condition is not None:
            _.append(clauses.Condition(self.node.condition))

        # repeat
        if self.node.repeat is not None:
            variables, expression = self.node.repeat
            if len(variables) != 1:
                raise ValueError(
                    "Cannot unpack more than one variable in a "
                    "repeat statement.")
            _.append(clauses.Repeat(variables[0], expression))

        content = self.node.content

        # macro slot definition
        if self.node.define_slot:
            # check if slot has been filled
            variable = self.symbols.slot + self.node.define_slot
            if variable in itertools.chain(*self.stream.scope):
                content = types.value(variable)

        # set dynamic content flag
        dynamic = content or self.node.translate is not None

        # static attributes are at the bottom of the food chain
        attributes = self.node.static_attributes

        # dynamic attributes
        attrs = self.node.dynamic_attributes or ()
        dynamic_attributes = tuple(attrs)

        for variables, expression in attrs:
            if len(variables) != 1:
                raise ValueError("Tuple definitions in assignment clause "
                                     "is not supported.")

            variable = variables[0]
            attributes[variable] = expression

        # translated attributes
        translated_attributes = self.node.translated_attributes or ()
        for variable, msgid in translated_attributes:
            if msgid:
                if variable in dynamic_attributes:
                    raise ValueError(
                        "Message id not allowed in conjunction with "
                        "a dynamic attribute.")

                value = types.value('"%s"' % msgid)

                if variable in attributes:
                    default = '"%s"' % attributes[variable]
                    expression = _translate(value, default=default)
                else:
                    expression = _translate(value)
            else:
                if variable in dynamic_attributes or variable in attributes:
                    text = '"%s"' % attributes[variable]
                    expression = _translate(text)
                else:
                    raise ValueError("Must be either static or dynamic "
                                     "attribute when no message id "
                                     "is supplied.")

            attributes[variable] = expression

        # tag
        if self.node.omit is not True:
            selfclosing = self.text is None and not dynamic and len(self) == 0
            tag = clauses.Tag(
                self.tag, attributes,
                expression=self.node.dict_attributes, selfclosing=selfclosing,
                cdata=self.node.cdata is not None)
            if self.node.omit:
                _.append(clauses.Condition(
                    _not(self.node.omit), [tag], finalize=False))
            else:
                _.append(tag)

        # tag text (if we're not replacing tag body)
        text = self.text
        if text and not dynamic:
            if isinstance(text, unicode):
                text = text.encode('utf-8')
            _.append(clauses.Out(text))

        # dynamic content
        if content:
            msgid = self.node.translate
            if msgid is not None:
                if msgid:
                    raise ValueError(
                        "Can't use message id with dynamic content translation.")
                
                _.append(clauses.Translate())
            _.append(clauses.Write(content))

        # use macro
        elif self.node.use_macro:
            # for each fill-slot element, create a new output stream
            # and save value in a temporary variable
            kwargs = []
            for element in self.xpath(
                './/*[@metal:fill-slot]', namespaces={'metal': config.METAL_NS}):
                variable = self.symbols.slot+element.node.fill_slot
                kwargs.append((variable, variable))
                
                subclauses = []
                subclauses.append(clauses.Define(
                    types.declaration((self.symbols.out, self.symbols.write)),
                    types.template('%(generation)s.initialize_stream()')))
                subclauses.append(clauses.Visit(element))
                subclauses.append(clauses.Assign(
                    types.template('%(out)s.getvalue()'), variable))
                _.append(clauses.Group(subclauses))
                
            _.append(clauses.Assign(self.node.use_macro, self.symbols.metal))

            # compute macro function arguments and create argument string
            arguments = ", ".join(
                tuple("%s=%s" % (arg, arg) for arg in \
                      itertools.chain(*self.stream.scope))+
                tuple("%s=%s" % kwarg for kwarg in kwargs))
                
            _.append(clauses.Write(
                types.value("%s(%s)" % (self.symbols.metal, arguments))))

        # translate body
        elif self.node.translate is not None:
            msgid = self.node.translate
            if not msgid:
                msgid = self._msgid()

            # for each named block, create a new output stream
            # and use the value in the translation mapping dict
            elements = [e for e in self if e.i18n_name]

            if elements:
                mapping = self.symbols.mapping
                _.append(clauses.Assign(types.value('{}'), mapping))
            else:
                mapping = 'None'

            for element in elements:
                name = element.i18n_name

                subclauses = []
                subclauses.append(clauses.Define(
                    types.declaration((self.symbols.out, self.symbols.write)),
                    types.template('%(generation)s.initialize_stream()')))
                subclauses.append(clauses.Visit(element))
                subclauses.append(clauses.Assign(
                    types.template('%(out)s.getvalue()'),
                    "%s['%s']" % (mapping, name)))

                _.append(clauses.Group(subclauses))

            _.append(clauses.Assign(
                _translate(types.value(repr(msgid)), mapping=mapping,
                           default=self.symbols.marker), self.symbols.result))

            # write translation to output if successful, otherwise
            # fallback to default rendition; 
            result = types.value(self.symbols.result)
            condition = types.template('%(result)s is not %(marker)s')
            _.append(clauses.Condition(condition,
                        [clauses.UnicodeWrite(result)]))

            subclauses = []
            if self.text:
                subclauses.append(clauses.Out(self.text.encode('utf-8')))
            for element in self:
                name = element.i18n_name
                if name:
                    value = types.value("%s['%s']" % (mapping, name))
                    subclauses.append(clauses.Write(value))
                else:
                    subclauses.append(clauses.Out(element.tostring()))
            if subclauses:
                _.append(clauses.Else(subclauses))

        return _

    def _wrap_literal(self, element):
        index = self.index(element)

        t = self.makeelement(utils.meta_attr('literal'))
        t.attrib[utils.meta_attr('omit-tag')] = ''
        t.tail = element.tail
        t.text = unicode(element)
        for child in element.getchildren():
            t.append(child)
        self.remove(element)
        self.insert(index, t)
        t.update()

    def _msgid(self):
        """Create an i18n msgid from the tag contents."""

        out = StringIO(self.text)
        for element in self:
            name = element.i18n_name
            if name:
                out.write("${%s}" % name)
                out.write(element.tail)
            else:
                out.write(element.tostring())

        msgid = out.getvalue().strip()
        msgid = msgid.replace('  ', ' ').replace('\n', '')
        
        return msgid

    def _pull_attribute(self, name, default=None):
        if name in self.attrib:
            value = self.attrib[name]
            del self.attrib[name]
            return value
        return default
    
    @property
    def node(self):
        return NotImplementedError("Must be provided by subclass.")

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
                expr = '%s string: %s' % (name, value)
                if attributes in self.attrib:
                    self.attrib[attributes] += '; %s' % expr
                else:
                    self.attrib[attributes] = expr

def translate_xml(body, parser, *args, **kwargs):
    root, doctype = parser.parse(body)
    return translate_etree(root, doctype=doctype, *args, **kwargs)

def translate_etree(root, macro=None, doctype=None,
                    params=[], default_expression='python'):
    if not isinstance(root, Element):
        raise ValueError("Must define valid namespace for tag: '%s.'" % root.tag)

    # skip to macro
    if macro is not None:
        elements = root.xpath(
            'descendant-or-self::*[@metal:define-macro="%s"]' % macro,
            namespaces={'metal': config.METAL_NS})

        if not elements:
            raise ValueError("Macro not found: %s." % macro)

        root = elements[0]
        del root.attrib[utils.metal_attr('define-macro')]
        
    # set default expression name
    if utils.get_namespace(root) == config.TAL_NS:
        tag = 'default-expression'
    else:
        tag = utils.tal_attr('default-expression')

    if not root.attrib.get(tag):
        root.attrib[tag] = default_expression

    # set up code generation stream
    if macro is not None:
        wrapper = generation.macro_wrapper
    else:
        wrapper = generation.template_wrapper

    # initialize code stream object
    stream = generation.CodeIO(
        root.symbols, indentation=1, indentation_string="\t")

    # initialize variable scope
    stream.scope.append(set(
        (stream.symbols.out, stream.symbols.write, stream.symbols.scope) + \
        tuple(params)))

    # output doctype if any
    if doctype and isinstance(doctype, (str, unicode)):
        dt = (doctype +'\n').encode('utf-8')
        doctype = clauses.Out(dt)
        stream.scope.append(set())
        stream.begin([doctype])
        stream.end([doctype])
        stream.scope.pop()

    # start generation
    root.start(stream)

    extra = ''

    # prepare args
    args = ', '.join(params)
    if args:
        args += ', '

    # prepare kwargs
    kwargs = ', '.join("%s=None" % param for param in params)
    if kwargs:
        kwargs += ', '

    # prepare selectors
    for selector in stream.selectors:
        extra += '%s=None, ' % selector

    # we need to ensure we have _context for the i18n handling in
    # the arguments. the default template implementations pass
    # this in explicitly.
    if stream.symbols.context not in params:
        extra += '%s=None, ' % stream.symbols.context

    code = stream.getvalue()

    class generator(object):
        @property
        def stream(self):
            return stream
        
        def __call__(self):
            parameters = dict(
                args=args, kwargs=kwargs, extra=extra, code=code)
            parameters.update(stream.symbols.__dict__)

            return wrapper % parameters, {stream.symbols.generation: generation}

    return generator()

def translate_text(body, parser, *args, **kwargs):
    root, doctype = parser.parse("<html xmlns='%s'></html>" % config.XHTML_NS)
    root.text = body
    root.attrib[utils.meta_attr('omit-tag')] = ''
    return translate_etree(root, doctype=doctype, *args, **kwargs)
    
def _translate(value, mapping=None, default=None):
    format = "_translate(%s, domain=%%(domain)s, mapping=%s, context=%%(context)s, " \
             "target_language=%%(language)s, default=%s)"
    return types.template(
        format % (value, mapping, default))

def _not(value):
    return types.value("not (%s)" % value)
