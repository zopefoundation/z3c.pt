from StringIO import StringIO
import lxml.etree

import io
import utils
import attributes as attrs
import clauses

wrapper = """\
def render(%starget_language=None):
\tglobal utils

\t_out = utils.initialize_stream()
\t_scope = locals().keys()
    
\t(_attributes, repeat) = utils.initialize_tal()
\t(_domain, _translate) = utils.initialize_i18n()
\t(_escape, _marker) = utils.initialize_helpers()

\t_target_language = target_language
%s
\treturn _out.getvalue()
"""

def attribute(ns, factory):
    def get(self):
        value = self.attrib.get(ns)
        if value is not None:
            return factory(value)
        
    return property(get)

class Element(lxml.etree.ElementBase):
    def begin(self, stream):
        stream.begin(self.clauses())
        
    def end(self, stream):
        stream.end(self.clauses())

    def body(self, stream):
        skip = self.replace or self.content or self.i18n_translate is not None
        if not skip:
            for element in self:
                element.visit(stream)
                        
    def visit(self, stream):
        self.begin(stream)
        self.body(stream)
        self.end(stream)

    def clauses(self):
        _ = []

        scope = utils.scope()

        # i18n domain
        if self.i18n_domain is not None:
            _.append(clauses.Define("_domain", [repr(self.i18n_domain)], scope))

        # defines
        if self.define is not None:
            for variables, expression in self.define:
                _.append(clauses.Define(variables, expression, scope))

        # condition
        if self.condition is not None:
            _.append(clauses.Condition(self.condition))

        # repeat
        if self.repeat is not None:
            variables, expression = self.repeat
            if len(variables) != 1:
                raise ValueError, "Cannot unpack more than one variable in a repeat statement."
            _.append(clauses.Repeat(variables[0], expression, scope))

        # tag tail (deferred)
        if self.tail:
            _.append(clauses.Out(self.tail, defer=True))
        
        # tag
        if self.replace is None:
            tag = clauses.Tag(self.tag, self._attributes())

            if self.omit is not None:
                _.append(clauses.Condition(_not(self.omit), [tag]))
            else:
                _.append(tag)

        # tag text (if we're not replacing tag body)
        if self.text and not (self.replace or self.content) and self.i18n_translate is None:
            _.append(clauses.Out(self.text))

        # dynamic content and content translation
        replace = self.replace
        content = self.content

        if replace and content:
            raise ValueError, "Can't use replace clause together with content clause."

        expression = replace or content
        if expression:
            if self.i18n_translate is not None:
                if self.i18n_translate != "":
                    raise ValueError, "Can't use message id with dynamic content translation."
                _.append(clauses.Translate())

            # TODO: structure
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
                    _.append(clauses.Assign(['{}'], mapping))
                else:
                    mapping = 'None'
                    
                for element in elements:
                    name = element.i18n_name
                    
                    subclauses = []
                    subclauses.append(clauses.Define('_out', ['utils.initialize_stream()'], scope))
                    subclauses.append(clauses.Group(element.clauses()))
                    subclauses.append(clauses.Assign(['_out.getvalue()'],
                                                     "%s['%s']" % (mapping, name)))

                    _.append(clauses.Group(subclauses))

                _.append(clauses.Assign(
                    _translate([repr(msgid)], mapping=mapping, default='_marker'),
                    '_result'))

                # write translation to output if successful, otherwise
                # fallback to default rendition; 

                _.append(clauses.Condition(['_result is not _marker'],
                                           [clauses.Write(['_result'])]))

                subclauses = []
                if self.text:
                    subclauses.append(clauses.Out(self.text))
                for element in self:
                    name = element.i18n_name
                    if name:
                        subclauses.append(clauses.Write(["%s['%s']" % (mapping, name)]))
                        #subclauses.append(clauses.Out(element.tail))
                    else:
                        subclauses.append(clauses.Out(lxml.etree.tostring(element)))

                if subclauses:
                    _.append(clauses.Else(subclauses))

        return _
    
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
            
    def _attributes(self):
        """Aggregate static, dynamic and translatable attributes."""

        attributes = {}

        # static attributes are at the bottom of the food chain
        static = [key for key in self.keys() if not key.startswith('{')]
        for key in static:
            attributes[key] = self.attrib[key]

        # dynamic attributes
        attrs = self.attributes
        if attrs is not None:
            for variables, expression in attrs:
                if len(variables) != 1:
                    raise ValueError, "Tuple definitions in assignment clause is not supported."

                variable = variables[0]
                attributes[variable] = _escape(expression, '"')
        else:
            attrs = []

        dynamic = [key for (key, expression) in attrs]

        # translated attributes
        if self.i18n_attributes:
            for variable, msgid in self.i18n_attributes:
                if variable in static:
                    static_expression = repr(attributes[variable])

                if msgid:
                    if variable in dynamic:
                        raise ValueError, "Message id not allowed in conjunction with " + \
                                          "a dynamic attribute."

                    expression = [repr(msgid)]

                    if variable in static:
                        expression = _translate(expression, default=static_expression)            
                    else:
                        expression = _translate(expression)
                else:
                    if variable in dynamic:
                        expression = _translate(attributes[variable])
                    elif variable in static:
                        expression = _translate(static_expression)                
                    else:
                        raise ValueError, "Must be either static or dynamic attribute " + \
                                          "when no message id is supplied."

                attributes[variable] = expression

        return attributes

    define = attribute(
        "{http://xml.zope.org/namespaces/tal}define", attrs.definitions)
    condition = attribute(
        "{http://xml.zope.org/namespaces/tal}condition", attrs.expression)
    repeat = attribute(
        "{http://xml.zope.org/namespaces/tal}repeat", attrs.definition)
    attributes = attribute(
        "{http://xml.zope.org/namespaces/tal}attributes", attrs.definitions)
    content = attribute(
        "{http://xml.zope.org/namespaces/tal}content", attrs.expression)
    replace = attribute(
        "{http://xml.zope.org/namespaces/tal}replace", attrs.expression)
    omit = attribute(
        "{http://xml.zope.org/namespaces/tal}omit-tag", attrs.expression)
    i18n_translate = attribute(
        "{http://xml.zope.org/namespaces/i18n}translate", attrs.name)
    i18n_attributes = attribute(
        "{http://xml.zope.org/namespaces/i18n}attrs", attrs.mapping)
    i18n_domain = attribute(
        "{http://xml.zope.org/namespaces/i18n}domain", attrs.name)
    i18n_name = attribute(
        "{http://xml.zope.org/namespaces/i18n}name", attrs.name)
    
# set up namespace
lookup = lxml.etree.ElementNamespaceClassLookup()
parser = lxml.etree.XMLParser()
parser.setElementClassLookup(lookup)

namespace = lxml.etree.Namespace('http://www.w3.org/1999/xhtml')
namespace[None] = Element

def translate(body, params=[]):
    tree = lxml.etree.parse(StringIO(body), parser)
    root = tree.getroot()

    stream = io.CodeIO(indentation=1, indentation_string="\t")

    root.visit(stream)

    code = stream.getvalue()
    args = ', '.join(params)
    if args: args += ', '
    
    return wrapper % (args, code), {'utils': utils}

def _translate(expressions, mapping=None, default=None):
    return [("_translate(%s, domain=_domain, mapping=%s, " + \
             "target_language=_target_language, default=%s)") %
            (exp, mapping, default) for exp in expressions]

def _escape(expressions, delim):
    return ["_escape(%s, '\\%s')" % (exp, delim) for exp in expressions]

def _not(expressions):
    return ["not (%s)" % exp for exp in expressions]