from zope import component

from StringIO import StringIO
import lxml.etree

import generation
import expressions
import clauses
import interfaces
import utils
import types

def attribute(ns, factory=None, default=None):
    def get(self):
        value = self.attrib.get(ns)
        if value is not None:
            if factory is None:
                return value

            f = factory(self._translator())
            return f(value)
        elif default is not None:
            return default
        
    def set(self, value):
        self.attrib[ns] = value

    return property(get, set)

class Element(lxml.etree.ElementBase):
    def begin(self, stream):
        stream.scope.append(set())
        stream.begin(self._clauses())
        
    def end(self, stream):
        stream.end(self._clauses())
        stream.scope.pop()

    def body(self, stream):
        skip = self.replace or self.content or self.i18n_translate is not None
        if not skip:
            for element in [e for e in self
                              if isinstance(e, lxml.etree._Comment)]:
                self._wrap_comment(element)

            seen = set()
            while len(seen) < len(self):
                element = set(self).difference(seen).pop()
                element.interpolate(stream)
                seen.add(element)
                
            for element in self:
                element.visit(stream)
                    
    def visit(self, stream):
        self.begin(stream)
        self.body(stream)
        self.end(stream)

    def interpolate(self, stream):
        """The current interpolation strategy is to translate the
        interpolation statements into TAL."""
        
        translator = self._translator()
        if self.text is not None:
            while self.text:
                m = translator.interpolate(self.text)
                if m is None:
                    break

                t = parser.makeelement(
                    '{http://xml.zope.org/namespaces/tal}interpolation')
                t.attrib['replace'] = m.group('expression')
                t.tail = self.text[m.end():]
                self.insert(0, t)

                if m.start() == 0:
                    self.text = self.text[1:m.start()+1]
                else:
                    self.text = self.text[:m.start()+1]

        # interpolate tail
        if self.tail is not None:
            while self.tail:
                m = translator.interpolate(self.tail)
                if m is None:
                    break

                t = parser.makeelement(
                    '{http://xml.zope.org/namespaces/tal}interpolation')
                t.attrib['replace'] = m.group('expression')
                t.tail = self.tail[m.end():]
                parent = self.getparent()
                parent.insert(parent.index(self)+1, t)

                self.tail = self.tail[:m.start()+len(m.group('prefix'))-1]
                
        # interpolate attributes
        for name in self._static_attributes():
            value = self.attrib[name]

            if translator.interpolate(value):
                del self.attrib[name]

                attributes = '{http://xml.zope.org/namespaces/tal}attributes'
                expr = '%s string: %s' % (name, value)
                if attributes in self.attrib:
                    self.attrib[attributes] += '; %s' % expr
                else:
                    self.attrib[attributes] = expr
                
    def _clauses(self):
        _ = []

        # i18n domain
        if self.i18n_domain is not None:
            _.append(clauses.Define(
                "_domain", types.value(repr(self.i18n_domain))))

        # defines
        if self.define is not None:
            for variables, expression in self.define:
                _.append(clauses.Define(variables, expression))

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

        # tag tail (deferred)
        if self.tail:
            _.append(clauses.Out(self.tail, defer=True))

        # compute dynamic flag
        dynamic = (self.replace or
                   self.content or
                   self.i18n_translate is not None)
        
        # tag
        if self.replace is None:
            selfclosing = self.text is None and not dynamic and len(self) == 0
            tag = clauses.Tag(self.tag, self._attributes(),
                              selfclosing=selfclosing)

            if self.omit:
                _.append(clauses.Condition(_not(self.omit), [tag],
                                           finalize=False))
            elif self.omit is not None:
                pass
            else:
                _.append(tag)

        # tag text (if we're not replacing tag body)
        if self.text and not dynamic:
            _.append(clauses.Out(self.text))

        # dynamic content and content translation
        replace = self.replace
        content = self.content

        if replace and content:
            raise ValueError("Can't use replace clause together with "
                             "content clause.")

        expression = replace or content
        if expression:
            if self.i18n_translate is not None:
                if self.i18n_translate != "":
                    raise ValueError("Can't use message id with "
                                     "dynamic content translation.")
                _.append(clauses.Translate())

            _.append(clauses.Write(expression))
        else:
            if self.i18n_translate is not None:
                msgid = self.i18n_translate
                if not msgid:
                    msgid = self._msgid()

                # for each named block, create a new output stream
                # and use the value in the translation mapping dict

                elements = [e for e in self if e.i18n_name]

                if elements:
                    mapping = '_mapping'
                    _.append(clauses.Assign(types.value('{}'), mapping))
                else:
                    mapping = 'None'
                    
                for element in elements:
                    name = element.i18n_name
                    
                    subclauses = []
                    subclauses.append(clauses.Define(
                        ('_out', '_write'),
                        types.value('generation.initialize_stream()')))
                    subclauses.append(clauses.Group(element._clauses()))
                    subclauses.append(clauses.Assign(
                        types.value('_out.getvalue()'),
                        "%s['%s']" % (mapping, name)))

                    _.append(clauses.Group(subclauses))

                _.append(clauses.Assign(
                    _translate(types.value(repr(msgid)), mapping=mapping,
                               default='_marker'), '_result'))

                # write translation to output if successful, otherwise
                # fallback to default rendition; 
                result = types.value('_result')
                condition = types.value('_result is not _marker')
                _.append(clauses.Condition(condition,
                            [clauses.UnicodeWrite(result)]))

                subclauses = []
                if self.text:
                    subclauses.append(clauses.Out(self.text))
                for element in self:
                    name = element.i18n_name
                    if name:
                        value = types.value("%s['%s']" % (mapping, name))
                        subclauses.append(clauses.Write(value))
                    else:
                        subclauses.append(clauses.Out(
                            lxml.etree.tostring(element)))

                if subclauses:
                    _.append(clauses.Else(subclauses))

        return _

    def _wrap_comment(self, element):
        index = self.index(element)

        t = parser.makeelement(
            '{http://xml.zope.org/namespaces/tal}comment')

        t.attrib['omit-tag'] = ''
        t.tail = element.tail
        t.text = '<!--' + element.text + '-->'

        for child in element.getchildren():
            t.append(child)

        self.remove(element)
        self.insert(index, t)
    
    def _msgid(self):
        """Create an i18n msgid from the tag contents."""

        out = StringIO(self.text)
        for element in self:
            name = element.i18n_name
            if name:
                out.write("${%s}" % name)
                out.write(element.tail)
            else:
                out.write(lxml.etree.tostring(element))

        msgid = out.getvalue().strip()
        msgid = msgid.replace('  ', ' ').replace('\n', '')
        
        return msgid

    def _static_attributes(self):
        attributes = {}

        for key in self.keys():
            if not key.startswith('{'):
                attributes[key] = self.attrib[key]

        return attributes
        
    def _attributes(self):
        """Aggregate static, dynamic and translatable attributes."""

        # static attributes are at the bottom of the food chain
        attributes = self._static_attributes()
        
        # dynamic attributes
        attrs = self.attributes
        if attrs is not None:
            for variables, expression in attrs:
                if len(variables) != 1:
                    raise ValueError("Tuple definitions in assignment clause "
                                     "is not supported.")

                variable = variables[0]
                attributes[variable] = expression
        else:
            attrs = []

        dynamic = [key for (key, expression) in attrs]

        # translated attributes
        if self.i18n_attributes:
            for variable, msgid in self.i18n_attributes:
                if msgid:
                    if variable in dynamic:
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
                    if variable in dynamic or variable in attributes:
                        text = '"%s"' % attributes[variable]
                        expression = _translate(text)
                    else:
                        raise ValueError("Must be either static or dynamic "
                                         "attribute when no message id "
                                         "is supplied.")

                attributes[variable] = expression

        return attributes

    def _translator(self):
        while self.default_expression is None:
            self = self.getparent()
            if self is None:
                raise ValueError("Default expression not set.")
            
        return component.getUtility(
            interfaces.IExpressionTranslation, name=self.default_expression)

    define = attribute(
        "{http://xml.zope.org/namespaces/tal}define", lambda p: p.definitions)
    condition = attribute(
        "{http://xml.zope.org/namespaces/tal}condition",
        lambda p: p.expression)
    repeat = attribute(
        "{http://xml.zope.org/namespaces/tal}repeat", lambda p: p.definition)
    attributes = attribute(
        "{http://xml.zope.org/namespaces/tal}attributes",
        lambda p: p.definitions)
    content = attribute(
        "{http://xml.zope.org/namespaces/tal}content", lambda p: p.output)
    replace = attribute(
        "{http://xml.zope.org/namespaces/tal}replace", lambda p: p.output)
    omit = attribute(
        "{http://xml.zope.org/namespaces/tal}omit-tag", lambda p: p.expression)
    i18n_translate = attribute(
        "{http://xml.zope.org/namespaces/i18n}translate")
    i18n_attributes = attribute(
        "{http://xml.zope.org/namespaces/i18n}attributes", lambda p: p.mapping)
    i18n_domain = attribute(
        "{http://xml.zope.org/namespaces/i18n}domain")
    i18n_name = attribute(
        "{http://xml.zope.org/namespaces/i18n}name")
    default_expression = attribute(
        "{http://xml.zope.org/namespaces/tal}default-expression")
    
class TALElement(Element):
    define = attribute("define", lambda p: p.definitions)
    condition = attribute("condition", lambda p: p.expression)
    replace = attribute("replace", lambda p: p.output)
    repeat = attribute("repeat", lambda p: p.definition)
    attributes = attribute("attributes", lambda p: p.expression)
    content = attribute("content", lambda p: p.output)
    omit = attribute("omit-tag", lambda p: p.expression, u"")
    default_expression = attribute("default-expression", lambda p: p.name)
    
    def _static_attributes(self):
        attributes = {}

        for key in self.keys():
            if key not in ('define',
                           'condition',
                           'replace',
                           'repeat',
                           'attributes',
                           'content',
                           'omit-tag'):
                raise ValueError(
                    u"Attribute '%s' not allowed in the namespace '%s'" %
                    (key, self.nsmap[self.prefix]))

        return attributes

# set up namespaces for XML parsing
lookup = lxml.etree.ElementNamespaceClassLookup()
parser = lxml.etree.XMLParser()
parser.setElementClassLookup(lookup)

try:
    lookup.get_namespace('http://www.w3.org/1999/xhtml')[None] = Element
    lookup.get_namespace('http://xml.zope.org/namespaces/tal'
                        )[None] = TALElement
except AttributeError:
    lxml.etree.Namespace('http://www.w3.org/1999/xhtml')[None] = Element
    lxml.etree.Namespace('http://xml.zope.org/namespaces/tal'
                        )[None] = TALElement

def translate_xml(body, *args, **kwargs):
    tree = lxml.etree.parse(StringIO(body), parser)
    root = tree.getroot()
    return translate_etree(root, *args, **kwargs)

def translate_etree(root, params=[], default_expression='python'):
    if None not in root.nsmap:
        raise ValueError, "Must set default namespace."

    # set default expression name
    key = '{http://xml.zope.org/namespaces/tal}default-expression'
    if key not in root.attrib:
        root.attrib[key] = default_expression

    # set up code generation stream
    generator = generation.Generator(params)
    stream = generator.stream

    # visit root
    root.interpolate(stream)
    root.visit(stream)

    return generator

def translate_text(body, *args, **kwargs):
    xml = parser.makeelement(
        '{http://www.w3.org/1999/xhtml}text',
        nsmap={None: 'http://www.w3.org/1999/xhtml'})
    xml.text = body
    xml.attrib['{http://xml.zope.org/namespaces/tal}omit-tag'] = ''
    return translate_etree(xml, *args, **kwargs)
    
def _translate(value, mapping=None, default=None):
    format = ("_translate(%s, domain=_domain, mapping=%s, context=_context, "
              "target_language=_target_language, default=%s)")
    return types.value(format % (value, mapping, default))

def _not(value):
    return types.value("not (%s)" % value)
