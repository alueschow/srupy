# coding: utf-8
"""Collects classes for SRU-specific entities.

:copyright: Copyright 2020 Andreas Lüschow
"""

from lxml import etree
from .util import get_namespace, etree_to_dict, etree_to_dict_without_ns


class SRURecord(object):
    """A generic SRU record.

    :param xml: XML representation of the record.
    :param strip_ns: Flag for whether to remove the namespaces from the
                     element names in the dictionary representation.
    """

    def __init__(self, xml, strip_ns=True):
        """Docstring."""
        super(SRURecord, self).__init__()

        #: The original parsed XML
        self.xml = xml
        self._strip_ns = strip_ns
        self._sru_namespace = get_namespace(self.xml)

    def __bytes__(self):
        """Docstring."""
        return etree.tounicode(self.xml).encode("utf8")

    def __str__(self):
        """Docstring."""
        return self.__unicode__()

    def __unicode__(self):
        """Docstring."""
        return etree.tounicode(self.xml)

    @property
    def raw(self):
        """Return the original XML as unicode."""
        return etree.tounicode(self.xml)


class Explain(SRURecord):
    """Represent a SRU Explain record.

    This object differs from the other entities in that is has to be created
    from a :class:`srupy.response.SRUResponse` instead of an XML element.
    :param explain_response: The response for an Explain request.
    :type explain_response: :class:`srupy.SRUResponse`
    """

    def __init__(self, explain_response):
        """Docstring."""
        super(Explain, self).__init__(explain_response.xml, strip_ns=True)
        self._explain_dict = self.get_explain_data()
        # TODO: Ist echoedExplainRequest vorgeschrieben bzw.
        #  im Standard vorgesehen?
        self.echo = EchoedRequest(self.xml.find(
            './/' + self._sru_namespace + 'echoedExplainRequest'))

    def __iter__(self):
        """Docstring."""
        return iter(self._explain_dict.items())

    def get_explain_data(self):
        """Docstring."""
        return etree_to_dict_without_ns(
            self.xml.find(
                './/' + self._sru_namespace + 'recordData'
            ).getchildren()[0]) \
            if self._strip_ns \
            else etree_to_dict(
            self.xml.find(
                './/' + self._sru_namespace + 'recordData'
            ).getchildren()[0])


class EchoedRequest(SRURecord):
    """Represent an SRU Echoed Request element.

    :param sru_xml: The SRU XML response.
    :type sru_xml: :class:`lxml.etree._Element`
    """

    def __init__(self, sru_xml):
        """Docstring."""
        super(EchoedRequest, self).__init__(sru_xml, strip_ns=True)

        _version = self.xml.find(self._sru_namespace + 'version')
        _query = self.xml.find(self._sru_namespace + 'query')
        _start_record = self.xml.find(self._sru_namespace + 'startRecord')
        _maximum_records = self.xml.find(
            self._sru_namespace + 'maximumRecords'
        )
        _record_xml_escaping = self.xml.find(
            self._sru_namespace + 'recordXMLEscaping'
        )
        _record_schema = self.xml.find(self._sru_namespace + 'recordSchema')
        _base_url = self.xml.find(self._sru_namespace + 'baseUrl')
        _xquery = self.xml.find(self._sru_namespace + 'xQuery')

        self.version = getattr(_version, 'text', None)
        self.query = getattr(_query, 'text', None)
        self.startRecord = getattr(_start_record, 'text', None)
        self.maximumRecords = getattr(_maximum_records, 'text', None)
        self.recordXMLEscaping = getattr(_record_xml_escaping, 'text', None)
        self.recordSchema = getattr(_record_schema, 'text', None)
        self.baseUrl = getattr(_base_url, 'text', None)
        self.xQuery = getattr(_xquery, 'text', None)

        self._echo_dict = {
            "version": self.version,
            "query": self.query,
            "startRecord": self.startRecord,
            "maximumRecords": self.maximumRecords,
            "recordXMLEscaping": self.recordXMLEscaping,
            "recordSchema": self.recordSchema,
            "baseUrl": self.baseUrl,
            "xQuery": self.xQuery
        }

    def __iter__(self):
        """Docstring."""
        return iter(self._echo_dict.items())


class Record(SRURecord):
    """Represent a SRU record.

    :param record_element: The XML element 'record'.
    :type record_element: :class:`lxml.etree._Element`
    :param strip_ns: Flag for whether to remove the namespaces from the
                     element names.
    """

    def __init__(self, record_element, strip_ns=True):
        """Docstring."""
        super(Record, self).__init__(record_element, strip_ns=strip_ns)
        self.record_data = self.get_record_data()

    def __iter__(self):
        """Docstring."""
        return iter(self.record_data.items())

    def get_record_data(self):
        """Docstring."""
        if self._strip_ns:
            return etree_to_dict_without_ns(
                self.xml.find(
                    './/' + self._sru_namespace + 'recordData'
                ).getchildren()[0])
        else:
            return etree_to_dict(
                self.xml.find(
                    './/' + self._sru_namespace + 'recordData'
                ).getchildren()[0])
