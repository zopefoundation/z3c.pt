import translation
import expressions
import utils
import config
import etree

class GenshiElement(translation.Element, translation.VariableInterpolation):
    """Genshi element.

    Implements the Genshi subset of the attribute template language.
    """

    translator = expressions.python_translation
    
    class node(translation.Node):
        @property
        def omit(self):
            if self.element.py_strip is not None:
                return self.element.py_strip or True
            if self.element.meta_omit is not None:
                return self.element.meta_omit or True
            if self.element.py_replace or self.element.meta_replace:
                return True
        
        @property
        def define(self):
            return self.element.py_with

        @property
        def condition(self):
            return self.element.py_if

        @property
        def repeat(self):
            return self.element.py_for

        @property
        def content(self):
            return self.element.py_content or self.element.py_replace or \
                   self.element.meta_replace

        @property
        def skip(self):
            return bool(self.content)
        
        @property
        def dict_attributes(self):
            return self.element.py_attrs

        @property
        def dynamic_attributes(self):
            return self.element.meta_attributes
        
        translated_attributes = None
        
        @property
        def static_attributes(self):
            return utils.get_attributes_from_namespace(
                self.element, config.XHTML_NS)

        translate = None
        translation_name = None
        translation_domain = None

        @property
        def macro(self):
            return self.element.py_def

        use_macro = None
        define_macro = None
        define_slot = None
        fill_slot = None

        @property
        def cdata(self):
            return self.element.meta_cdata

    node = property(node)

    def update(self):
        # Step 1: Convert py:choose, py:when, py:otherwise into
        # tal:define, tal:condition
        stream = self.stream
        choose_expression = self._pull_attribute(utils.py_attr('choose'))
        if choose_expression is not None:
            choose_variable = stream.save()
            
            if choose_expression:
                self._add_define(choose_variable, choose_expression)
                
            # select all elements that have the "py:when" controller,
            # unless a "py:choose" expression sits in-between
            variables = []
            for element in self.xpath(
                './*[@py:when]|.//*[not(@py:choose)]/*[@py:when]',
                namespaces={'py': config.PY_NS}):

                expression = element._pull_attribute(utils.py_attr('when'))
                variable = stream.save()
                variables.append(variable)

                # add definition to ancestor
                self._add_define(variable, expression)
                
                # add condition to element
                if choose_expression:
                    expression = "python: %s == %s" % (
                        choose_variable, variable)
                else:
                    expression = "python: %s" % variable
                    
                element.attrib[utils.py_attr('if')] = expression

            # process any "py:otherwise"-controllers
            for element in self.xpath(
                './*[@py:otherwise]|.//*[not(@py:choose)]/*[@py:otherwise]',
                namespaces={'py': config.PY_NS}):
                if choose_expression:
                    expression = "python: %s not in %s" % (
                        choose_variable, repr(tuple(variables)))
                else:
                    expression = "python: not(%s)" % " or ".join(variables)
                    
                element.attrib[utils.py_attr('if')] = expression

        # Step 2: Process "py:match" macros
        for element in self:
            if getattr(element, 'py_match', None) is None:
                continue
            
            nsmap = element.nsmap.copy()

            # default namespace is not allowed in XPath
            nsmap['xmlns'] = nsmap[None]
            del nsmap[None]

            # define macro
            name = stream.save()
            element.attrib[utils.py_attr('def')] = "%s(select)" % name

            matches = self.getroottree().getroot().xpath(
                element.py_match, namespaces=nsmap)
            for match in matches:
                # save reference to bound xpath-function
                select = stream.save()
                stream.selectors[select] = match.xpath

                # replace matched element with macro
                expression = "%s(%s)" % (name, select)
                match.attrib[utils.py_attr('replace')] = expression

                # save select-variable as element attribute
                match.attrib[utils.meta_attr('select')] = select

        # Step 3: Variable interpolation
        translation.VariableInterpolation.update(self)        

    def _add_define(self, variable, expression):
        name = utils.py_attr('with')
        define = "%s=%s; " % (variable, expression)

        if name in self.attrib:
            self.attrib[name] += define
        else:
            self.attrib[name] = define

    def _pull_attribute(self, name, default=None):
        attrib = self.attrib
        if name in attrib:
            value = attrib[name]
            del attrib[name]
            return value
        return default    

class XHTMLElement(GenshiElement):
    """XHTML namespace element."""

    py_if = utils.attribute(
        utils.py_attr('if'), lambda p: p.expression)
    py_for = utils.attribute(
        utils.py_attr('for'), lambda p: p.definition)
    py_with = utils.attribute(utils.py_attr('with'),
        lambda p: expressions.python_translation.definitions)
    py_choose = utils.attribute(
        utils.py_attr('choose'), lambda p: p.expression)
    py_when = utils.attribute(
        utils.py_attr('when'), lambda p: p.expression)
    py_match = utils.attribute(
        utils.py_attr('match'))
    py_def = utils.attribute(
        utils.py_attr('def'), lambda p: p.method)
    py_attrs = utils.attribute(
        utils.py_attr('attrs'), lambda p: p.expression)
    py_content = utils.attribute(
        utils.py_attr('content'), lambda p: p.output)
    py_replace = utils.attribute(
        utils.py_attr('replace'), lambda p: p.output)
    py_strip = utils.attribute(
        utils.py_attr('strip'), lambda p: p.expression)

class PyElement(XHTMLElement):
    py_strip = utils.attribute("strip", lambda p: p.expression, u"")
    
class PyIfElement(PyElement):
    py_if = utils.attribute("test", lambda p: p.expression)

class PyForElement(PyElement):
    py_for = utils.attribute("each", lambda p: p.definition)

class PyWithElement(PyElement):
    py_with = utils.attribute(
        "vars", lambda p: expressions.python_translation.definitions)

class PyDefElement(PyElement):
    py_def = utils.attribute("function", lambda p: p.method)

class PyMatchElement(PyElement):
    py_match = utils.attribute("path")
    
class GenshiParser(etree.Parser):
    """ The parser implementation for Genshi templates """
    element_mapping = {
        config.XHTML_NS: {None: XHTMLElement},
        config.META_NS: {None: XHTMLElement},
        config.PY_NS: {'if': PyIfElement,
                       'for': PyForElement,
                       'def': PyDefElement,
                       'with': PyWithElement,
                       'match': PyMatchElement}}
