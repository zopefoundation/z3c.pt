from chameleon.core import translation
from chameleon.core import config
from chameleon.core import utils

import chameleon.zpt.language

class ZopePageTemplateElement(chameleon.zpt.language.ZopePageTemplateElement):
    meta_interpolation = utils.attribute(
        utils.meta_attr('interpolation'), default="false", recursive=True)

class XHTMLElement(chameleon.zpt.language.XHTMLElement):
    meta_interpolation = utils.attribute(
        utils.meta_attr('interpolation'), default="false", recursive=True)

class TALElement(chameleon.zpt.language.TALElement):
    meta_interpolation = utils.attribute(
        utils.meta_attr('interpolation'), default="false", recursive=True)

class METALElement(chameleon.zpt.language.METALElement):
    meta_interpolation = utils.attribute(
        utils.meta_attr('interpolation'), default="false", recursive=True)

class MetaElement(chameleon.zpt.language.MetaElement):
    meta_interpolation = utils.attribute(
        utils.meta_attr('interpolation'), default="false", recursive=True)

class Parser(chameleon.zpt.language.Parser):
    """Zope Page Template parser."""

    element_mapping = {
        config.XHTML_NS: {None: XHTMLElement},
        config.META_NS: {None: MetaElement},
        config.TAL_NS: {None: TALElement},
        config.METAL_NS: {None: METALElement}}

    fallback = XHTMLElement
    default_expression = 'path'
