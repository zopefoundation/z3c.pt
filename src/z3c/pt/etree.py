import htmlentitydefs
import config
import utils
import cgi
import copy
from StringIO import StringIO

def import_elementtree():
    try:
        import xml.etree.ElementTree as ET
    except:
        try:
            import elementtree.ElementTree as ET
        except ImportError:
            import cElementTree as ET
        
    return ET

class Parser(object):
    element_mapping = utils.emptydict()

    def parse(self, body):
        return parse(body, self.element_mapping)
        
try:
    import lxml.etree

    class ElementBase(lxml.etree.ElementBase):
        def tostring(self):
            return lxml.etree.tostring(self)

        def _convert_cdata_sections(self):
            start = '<![CDATA['
            end = ']]>'

            text = self._raw_text or ""
            tail = self._raw_tail or ""

            if start in text:
                before, rest = text.split(start, 1)
                cdata, after = rest.split(end, 1)

                element = self.makeelement(
                    utils.xhtml_attr('cdata'))
                element.attrib[utils.meta_attr('cdata')] = ""
                element.text = cdata
                element.tail = after
                
                self.text = before
                self.insert(0, element)
                element._convert_cdata_sections()
                
            if start in tail:
                before, rest = tail.split(start, 1)
                cdata, after = rest.split(end, 1)

                element = self.makeelement(
                    utils.xhtml_attr('cdata'))
                element.attrib[utils.meta_attr('cdata')] = ""
                self.addnext(element)

                element.text = cdata
                element.tail = after
                self.tail = before
                element._convert_cdata_sections()
                
        @property
        def _raw_text(self):
            """Return raw text.

            CDATA sections are returned in their original formatting;
            the routine relies on the fact that ``tostring`` will
            output CDATA sections even though they're not present in
            the .text-attribute.
            """

            if self.text in ("", None):
                return self.text
            
            elements = tuple(self)
            del self[:]
            xml = lxml.etree.tostring(self, encoding='utf-8', with_tail=False)
            self.extend(elements)
                
            element = self.makeelement(self.tag, nsmap=self.nsmap)
            for attr, value in self.items():
                element.attrib[attr] = value

            html = lxml.etree.tostring(element)
            tag = len(element.tag.split('}')[-1])+3
            text = xml[len(html)-tag:-tag]

            return text

        @property
        def _raw_tail(self):
            """Return raw tail.

            CDATA sections are returned in their original formatting;
            the routine relies on the fact that ``tostring`` will
            output CDATA sections even though they're not present in
            the .tail-attribute.
            """

            if self.tail in ("", None):
                return self.tail

            elements = tuple(self)
            del self[:]

            parent = self.getparent()
            if parent is None:
                return self.tail
            
            length = len(lxml.etree.tostring(self, encoding='utf-8', with_tail=False))
            
            # wrap element
            index = parent.index(self)
            element = self.makeelement(self.tag, nsmap=self.nsmap)
            element.append(self)
            xml = lxml.etree.tostring(element, encoding='utf-8', with_tail=False)
            self.extend(elements)
            parent.insert(index, self)

            ns = self.tag[self.tag.find('{')+1:self.tag.find('}')]
            for prefix, namespace in self.nsmap.items():
                if ns == namespace:
                    if prefix is None:
                        tag = len(self.tag) - len(ns)
                    else:
                        tag = len(self.tag) - len(ns) + len(prefix) + 1
                    break
            else:
                raise ValueError(
                    "Unable to determine tag length: %s." % self.tag)
                
            tail = xml[length+tag:-tag-1]
            
            return tail

    def convert_cdata_section(node):
        parent = node.getparent()
        if parent is not None:
            index = parent.index(node)
            element = node.makeelement(node.tag, nsmap=node.nsmap)
            element.append(node)
            xml = lxml.etree.tostring(element, encoding='utf-8', with_tail=False)
            parent.insert(index, node)
        else:
            xml = lxml.etree.tostring(node, encoding='utf-8', with_tail=False)
            
        if 'CDATA' in xml:
            node._convert_cdata_sections()
            for child in tuple(node):
                convert_cdata_section(child)
        
    def parse(body, element_mapping):
        lookup = lxml.etree.ElementNamespaceClassLookup()
        parser = lxml.etree.XMLParser(resolve_entities=False, strip_cdata=False)
        parser.setElementClassLookup(lookup)

        # lxml 1.3-compatibility
        try:
            ns_lookup = lookup.get_namespace
        except AttributeError:
            ns_lookup = lxml.etree.Namespace

        for key, mapping in element_mapping.items():
            ns_lookup(key).update(mapping)
        
        tree = lxml.etree.parse(StringIO(body), parser)
        root = tree.getroot()

        convert_cdata_section(root)
        
        return root, tree.docinfo.doctype

except ImportError:
    ET = import_elementtree()
    from pdis.xpath import XPath
    
    class ElementBase(object, ET._ElementInterface):
        _parent = None
        
        def __new__(cls, tag, attrs=None):
            return element_factory(tag, attrs)

        def __init__(self, tag, attrs=None):
            if attrs is None:
                attrs = {}
            
            ET._ElementInterface.__init__(self, tag, attrs)
            
        def getparent(self):
            return self._parent

        def getroottree(self):
            while self._parent is not None:
                self = self._parent
            class roottree(object):
                @classmethod
                def getroot(cls):
                    return self
            return roottree
            
        def insert(self, position, element):
            element._parent = self
            ET._ElementInterface.insert(self, position, element)

        def tostring(self):
            return ET.tostring(self)

        def xpath(self, path, namespaces={}):
            xpath = XPath(path, namespace_mapping=namespaces)
            return xpath.evaluate(self)
            
        @property
        def nsmap(self):
            # TODO: Return correct namespace map
            return {None: config.XHTML_NS}

        @property
        def prefix(self):
            try:
                ns, prefix = self.tag.split('}')
            except:
                return None
            
            for prefix, namespace in self.nsmap.items():
                if namespace == ns:
                    return prefix
            
    namespaces = {}
    def ns_lookup(ns):
        return namespaces.setdefault(ns, {})

    class TreeBuilder(ET.TreeBuilder):
        def start(self, tag, attrs):
            if len(self._elem):
                parent = self._elem[-1]
            else:
                parent = None
            elem = ET.TreeBuilder.start(self, tag, attrs)
            elem._parent = parent
            elem.makeelement = self._factory
            
    class XMLParser(ET.XMLParser):
        def __init__(self, **kwargs):
            ET.XMLParser.__init__(self, **kwargs)

            # this makes up for ET's lack of support for comments and
            # processing instructions
            self._parser.CommentHandler = self.handle_comment
            self._parser.ProcessingInstructionHandler = self.handle_pi
            self._parser.StartCdataSectionHandler = self.handle_cdata_start
            self._parser.EndCdataSectionHandler = self.handle_cdata_end
       
        def doctype(self, name, pubid, system):
            self.doctype = u'<!DOCTYPE %(name)s PUBLIC "%(pubid)s" "%(system)s">' % \
                           dict(name=name, pubid=pubid, system=system)

        def handle_comment(self, data):
            name = utils.tal_attr('comment')
            self._target.start(name, {})
            self._target.data("<!-- %s -->" % data)
            self._target.end(name)

        def handle_pi(self, target, data):
            name = utils.tal_attr('pi')
            self._target.start(name, {})
            self._target.data("<?%(target)s %(data)s?>" % dict(target=target, data=data))
            self._target.end(name)

        def handle_cdata_start(self):
            self._target.start(utils.xhtml_attr('cdata'), {
                utils.tal_attr('cdata'): ''})

        def handle_cdata_end(self):
            self._target.end(utils.xhtml_attr('cdata'))
            
    def parse(body, element_mapping):
        def element_factory(tag, attrs=None, nsmap=None):
            if attrs is None:
                attrs = {}

            if '{' in tag:
                ns = tag[tag.find('{')+1:tag.find('}')]
                ns_tag = tag[tag.find('}')+1:]
            else:
                ns = None
                ns_tag = None

            namespace = element_mapping[ns]
            factory = namespace.get(ns_tag) or namespace.get(None) or ElementBase

            element = object.__new__(factory)
            element.__init__(tag, attrs)

            return element
        
        target = TreeBuilder(element_factory=element_factory)
        parser = XMLParser(target=target)
        parser.entity = dict([(name, "&%s;" % name) for name in htmlentitydefs.entitydefs])
        parser.feed(body)
        root = parser.close()

        return root, parser.doctype
