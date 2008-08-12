import htmlentitydefs
import config
import utils
from StringIO import StringIO

try:
    import lxml.etree

    lookup = lxml.etree.ElementNamespaceClassLookup()
    parser = lxml.etree.XMLParser(resolve_entities=False, strip_cdata=False)
    parser.setElementClassLookup(lookup)

    # lxml 1.3-compatibility
    try:
        ns_lookup = lookup.get_namespace
    except AttributeError:
        ns_lookup = lxml.etree.Namespace

    class ElementBase(lxml.etree.ElementBase):
        def tostring(self):
            return lxml.etree.tostring(self)

        @property
        def raw_text(self):
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

            element = parser.makeelement(self.tag, nsmap=self.nsmap)
            for attr, value in self.items():
                element.attrib[attr] = value

            html = lxml.etree.tostring(element)                
            text = xml[len(html)-1:-len(element.tag[element.tag.rfind('}'):])-2]

            return text

        @property
        def raw_tail(self):
            """Return raw text.

            CDATA sections are returned in their original formatting;
            the routine relies on the fact that ``tostring`` will
            output CDATA sections even though they're not present in
            the .text-attribute.
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
            element = parser.makeelement(self.tag, nsmap=self.nsmap)
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
            
    element_factory = parser.makeelement

    def parse(body):
        tree = lxml.etree.parse(StringIO(body), parser)
        root = tree.getroot()
        return root, tree.docinfo.doctype

except ImportError:
    import xml.etree.ElementTree
    import html5lib.treebuilders.etree
    
    class ElementBase(object, xml.etree.ElementTree._ElementInterface):
        _parent = None
        
        def __new__(cls, tag, attrs=None):
            return element_factory(tag, attrs)

        def __init__(self, tag, attrs=None):
            if attrs is None:
                attrs = {}
            
            xml.etree.ElementTree._ElementInterface.__init__(self, tag, attrs)
            
        def getparent(self):
            return self._parent

        def insert(self, position, element):
            element._parent = self
            xml.etree.ElementTree._ElementInterface.insert(self, position, element)

        def tostring(self):
            return xml.etree.ElementTree.tostring(self)

        def xpath(self, expression, namespaces={}):
            return []
            
        @property
        def nsmap(self):
            return {None: config.XML_NS}
        
    namespaces = {}
    def ns_lookup(ns):
        return namespaces.setdefault(ns, {})

    class TreeBuilder(xml.etree.ElementTree.TreeBuilder):
        def start(self, tag, attrs):
            if len(self._elem):
                parent = self._elem[-1]
            else:
                parent = None
            elem = xml.etree.ElementTree.TreeBuilder.start(self, tag, attrs)
            elem._parent = parent

    class XMLParser(xml.etree.ElementTree.XMLParser):
        def __init__(self, **kwargs):
            xml.etree.ElementTree.XMLParser.__init__(self, **kwargs)

            # this makes up for ET's lack of support for comments and
            # processing instructions
            self._parser.CommentHandler = self.handle_comment
            self._parser.ProcessingInstructionHandler = self.handle_pi
            #self._target.start("document", {})
       
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

    def element_factory(tag, attrs=None, nsmap=None):
        if attrs is None:
            attrs = {}

        if '{' in tag:
            ns = tag[tag.find('{')+1:tag.find('}')]
            ns_tag = tag[tag.find('}')+1:]
        else:
            ns = None
            ns_tag = None

        namespace = ns_lookup(ns)
        factory = namespace.get(ns_tag) or namespace.get(None) or Element
            
        element = object.__new__(factory)
        element.__init__(tag, attrs)
        return element
        #return factory(tag, attrs)

    def parse(body):
        target = TreeBuilder(element_factory=element_factory)

        parser = XMLParser(target=target)
        parser.entity = dict([(name, "&%s;" % name) for name in htmlentitydefs.entitydefs])
        parser.feed(body)
        root = parser.close()

        return root, parser.doctype

    def CDATA(text):
        return text
