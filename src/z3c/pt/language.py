from chameleon.core import translation
from chameleon.core import config
from chameleon.core import utils

import chameleon.zpt.language


class ZopePageTemplateElement(chameleon.zpt.language.ZopePageTemplateElement):
    """Zope Page Template element.

    Implements the ZPT subset of the attribute template language.
    """
    meta_interpolation = utils.attribute(
        utils.meta_attr('interpolation'), default="false")

class XHTMLElement(chameleon.zpt.language.XHTMLElement):
    """XHTML namespace element."""
    meta_interpolation = utils.attribute(
        utils.meta_attr('interpolation'), default="false")

class TALElement(chameleon.zpt.language.TALElement):
    """TAL namespace element."""
    meta_interpolation = utils.attribute(
        utils.meta_attr('interpolation'), default="false")

class METALElement(chameleon.zpt.language.METALElement):
    """METAL namespace element."""
    meta_interpolation = utils.attribute(
        utils.meta_attr('interpolation'), default="false")

class MetaElement(chameleon.zpt.language.MetaElement):
    meta_interpolation = utils.attribute(
        utils.meta_attr('interpolation'), default="false")

class Parser(chameleon.zpt.language.Parser):
    """Zope Page Template parser."""

    element_mapping = {
        config.XHTML_NS: {None: XHTMLElement},
        config.META_NS: {None: MetaElement},
        config.TAL_NS: {None: TALElement},
        config.METAL_NS: {None: METALElement}}

    fallback = XHTMLElement
    default_expression = 'path'
