# coding: utf-8
"""SRU Response object.

:copyright: Copyright 2020 Andreas Lüschow
"""

from lxml import etree

XMLParser = etree.XMLParser(
    remove_blank_text=True,
    recover=True,
    resolve_entities=False
)


class SRUResponse(object):
    """A response from an SRU server.

    Provides access to the returned data on different abstraction
    levels.
    :param http_response: The original HTTP response.
    :param params: The SRU parameters for the request.
    :type params: dict
    """

    def __init__(self, http_response, params):
        """Docstring."""
        self.params = params
        self.http_response = http_response

    @property
    def raw(self):
        """Return the server's response as unicode."""
        return self.http_response.text

    @property
    def xml(self):
        """Return the server's response as parsed XML."""
        return etree.XML(self.http_response.content,
                         parser=XMLParser)
