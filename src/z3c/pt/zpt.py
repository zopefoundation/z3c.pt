from zope import component

import translation
import interfaces
import utils
import config
import etree

class ZopePageTemplateElement(
    translation.Element, translation.VariableInterpolation):
    """Zope Page Template element.

    Implements the ZPT subset of the attribute template language.
    """

    class node(translation.Node):
        @property
        def omit(self):
            if self.element.tal_omit is not None:
                return self.element.tal_omit or True
            if self.element.meta_omit is not None:
                return self.element.meta_omit or True
            if self.element.tal_replace or self.element.meta_replace:
                return True
            if self.element.metal_use or self.element.metal_fillslot:
                return True
            
        @property
        def define(self):
            return self.element.tal_define

        @property
        def condition(self):
            return self.element.tal_condition

        @property
        def repeat(self):
            return self.element.tal_repeat

        @property
        def content(self):
            return self.element.tal_content or self.element.tal_replace or \
                   self.element.meta_replace

        @property
        def skip(self):
            return self.content or self.define_macro or \
                   self.use_macro or self.translate is not None

        dict_attributes = None

        @property
        def dynamic_attributes(self):
            return (self.element.tal_attributes or ()) + \
                   (self.element.meta_attributes or ())

        @property
        def translated_attributes(self):
            return self.element.i18n_attributes
        
        @property
        def static_attributes(self):
            return utils.get_attributes_from_namespace(
                self.element, config.XHTML_NS)
            
        @property
        def translate(self):
            return self.element.i18n_translate

        @property
        def translation_name(self):
            return self.element.i18n_name

        @property
        def translation_domain(self):
            return self.element.i18n_domain

        macro = None
        
        @property
        def use_macro(self):
            return self.element.metal_use
        
        @property
        def define_macro(self):
            return self.element.metal_define

        @property
        def define_slot(self):
            return self.element.metal_defineslot

        @property
        def fill_slot(self):
            return self.element.metal_fillslot        

        @property
        def cdata(self):
            return self.element.meta_cdata

        @property
        def default_expression(self):
            return self.element.tal_default_expression

        include = None
        format = None
        
    node = property(node)

    @property
    def translator(self):
        while self.node.default_expression is None:
            self = self.getparent()
            if self is None:
                raise ValueError("Default expression not set.")
            
        return component.getUtility(
            interfaces.IExpressionTranslation, name=self.node.default_expression)

    def update(self):
        translation.VariableInterpolation.update(self)        

class XHTMLElement(ZopePageTemplateElement):
    """XHTML namespace element."""

    tal_define = utils.attribute(
        utils.tal_attr('define'), lambda p: p.definitions)
    tal_condition = utils.attribute(
        utils.tal_attr('condition'), lambda p: p.expression)
    tal_repeat = utils.attribute(
        utils.tal_attr('repeat'), lambda p: p.definition)
    tal_attributes = utils.attribute(
        utils.tal_attr('attributes'), lambda p: p.definitions)
    tal_content = utils.attribute(
        utils.tal_attr('content'), lambda p: p.output)
    tal_replace = utils.attribute(
        utils.tal_attr('replace'), lambda p: p.output)
    tal_omit = utils.attribute(
        utils.tal_attr('omit-tag'), lambda p: p.expression)
    tal_default_expression = utils.attribute(
        utils.tal_attr('default-expression'))
    metal_define = utils.attribute(
        utils.metal_attr('define-macro'), lambda p: p.method)
    metal_use = utils.attribute(
        utils.metal_attr('use-macro'), lambda p: p.expression)
    metal_fillslot = utils.attribute(
        utils.metal_attr('fill-slot'))
    metal_defineslot = utils.attribute(
        utils.metal_attr('define-slot'))
    i18n_translate = utils.attribute(
        utils.i18n_attr('translate'))
    i18n_attributes = utils.attribute(
        utils.i18n_attr('attributes'), lambda p: p.mapping)
    i18n_domain = utils.attribute(
        utils.i18n_attr('domain'))
    i18n_name = utils.attribute(
        utils.i18n_attr('name'))

class TALElement(ZopePageTemplateElement):
    """TAL namespace element."""
    
    tal_define = utils.attribute("define", lambda p: p.definitions)
    tal_condition = utils.attribute("condition", lambda p: p.expression)
    tal_replace = utils.attribute("replace", lambda p: p.output)
    tal_repeat = utils.attribute("repeat", lambda p: p.definition)
    tal_attributes = utils.attribute("attributes", lambda p: p.expression)
    tal_content = utils.attribute("content", lambda p: p.output)
    tal_omit = utils.attribute("omit-tag", lambda p: p.expression, u"")
    tal_default_expression = utils.attribute(
        'default-expression')
    tal_cdata = utils.attribute("cdata")

    metal_define = None
    metal_use = None
    metal_fillslot = None
    metal_defineslot = None
    i18n_domain = None
    i18n_translate = None
    i18n_attributes = None
    
class METALElement(ZopePageTemplateElement):
    """METAL namespace element."""

    tal_default_expression = utils.attribute(
        utils.tal_attr('default-expression'))
    metal_define = utils.attribute('define-macro', lambda p: p.method)
    metal_use = utils.attribute('use-macro', lambda p: p.expression)
    metal_fillslot = utils.attribute('fill-slot')
    metal_defineslot = utils.attribute('define-slot')

class ZopePageTemplateParser(etree.Parser):
    """ The parser implementation for ZPT """
    element_mapping = {
        config.XHTML_NS: {None: XHTMLElement},
        config.META_NS: {None: XHTMLElement},
        config.TAL_NS: {None: TALElement},
        config.METAL_NS: {None: METALElement}}

    default_expression = 'python'

    def __init__(self, default_expression=None):
        if default_expression is not None:
            self.default_expression = default_expression

    def parse(self, body):
        root, doctype = super(ZopePageTemplateParser, self).parse(body)

        # if a default expression is not set explicitly in the
        # template, use the TAL-attribute ``default-expression``
        # to set it
        if utils.get_namespace(root) == config.TAL_NS:
            tag = 'default-expression'
        else:
            tag = utils.tal_attr('default-expression')

        if not root.attrib.get(tag):
            root.attrib[tag] = self.default_expression

        return root, doctype
