# coding: utf-8
"""A SRU client.

:copyright: Copyright 2020 Andreas Lüschow
"""
import inspect
import logging
import time

import requests

from srupy.iterator import BaseSRUIterator, SRUResponseIterator
from srupy.response import SRUResponse
from .models import Explain

logger = logging.getLogger(__name__)

SRU_NAMESPACE = '{http://docs.oasis-open.org/ns/search-ws/sruResponse}'


class SRUpy(object):
    """Client for sending SRU requests.

    Use it like this::
        >>> py_sru = SRUpy('http://elis.da.ulcc.ac.uk/cgi/oai2')
        >>> records = py_sru.get_records()
        >>> records.next()
    :param endpoint: The endpoint of the SRU server.
    :type endpoint: str
    :param http_method: Method used for requests (GET or POST, default: GET).
    :type http_method: str
    :param protocol_version: The SRU protocol version.
    :type protocol_version: str
    :param iterator: The type of the returned iterator
           (default: :class:`srupy.iterator.SRUResponseIterator`)
    :param max_retries: Number of retry attempts if an HTTP
                        request fails (default: 0 = request
                        only once). SRUpy will use the value
                        from the retry-after header (if present)
                        and will wait the specified number of
                        seconds between retries.
    :type max_retries: int
    :param retry_status_codes:  HTTP status codes to
                                retry (default will only retry on 503)
    :type retry_status_codes: iterable
    :param default_retry_after: default number of seconds to wait
                                between retries in case no retry-after
                                header is found on the response
                                (defaults to 60 seconds)
    :type default_retry_after: int
    :param encoding:    Can be used to override the encoding used
                        when decoding the server response. If not
                        specified, `requests` will use the encoding
                        returned by the server in the `content-type`
                        header. However, if the `charset`
                        information is missing, `requests` will fallback to
                        `'ISO-8859-1'`.
    :type encoding:      str
    :param request_args: Arguments to be passed to requests when issuing HTTP
                         requests. See the `documentation of requests
                         <http://docs.python-requests.org/en/master/api/#main-interface>`_
                         for all available parameters.
    """

    def __init__(self, endpoint,
                 http_method='GET',
                 protocol_version='2.0',
                 iterator=SRUResponseIterator,
                 max_retries=0,
                 retry_status_codes=None,
                 default_retry_after=60,
                 encoding=None,
                 **request_args):
        """Docstring."""
        self.endpoint = endpoint
        if http_method not in ['GET', 'POST']:
            raise ValueError("Invalid HTTP method: %s! Must be GET or POST.")
        if protocol_version not in ['2.0', '1.2', '1.1']:
            raise ValueError(
                "Invalid protocol version: %s! Must be 2.0, 1.2 or 1.1")
        self.http_method = http_method
        self.protocol_version = protocol_version
        if inspect.isclass(iterator) and issubclass(iterator, BaseSRUIterator):
            self.iterator = iterator
        else:
            raise TypeError(
                "Argument 'iterator' must be subclass of %s"
                % BaseSRUIterator.__name__)
        self.max_retries = max_retries
        self.retry_status_codes = retry_status_codes or [503]
        self.default_retry_after = default_retry_after
        self.sru_namespace = SRU_NAMESPACE
        self.encoding = encoding
        self.request_args = request_args

    def harvest(self, **kwargs):
        """Make HTTP requests to the SRU server.

        :param kwargs: SRU HTTP parameters.
        :rtype: :class:`srupy.SRUResponse`
        """
        http_response = self._request(kwargs)
        for _ in range(self.max_retries):
            if self._is_error_code(http_response.status_code) \
                    and http_response.status_code in self.retry_status_codes:
                retry_after = self.get_retry_after(http_response)
                logger.warning(
                    "HTTP %d! Retrying after %d seconds..."
                    % (http_response.status_code, retry_after))
                time.sleep(retry_after)
                http_response = self._request(kwargs)
        http_response.raise_for_status()
        if self.encoding:
            http_response.encoding = self.encoding
        return SRUResponse(http_response, params=kwargs)

    def _request(self, kwargs):
        """Docstring."""
        if self.http_method == 'GET':
            return requests.get(self.endpoint,
                                params=kwargs, **self.request_args)
        return requests.post(self.endpoint,
                             data=kwargs, **self.request_args)

    def get_records(self, **kwargs):
        """Issue a SRU request to fetch records.

        :rtype: :class:`srupy.iterator.BaseSRUIterator`
        """
        # TODO: Default Parameter hier eintragen
        # Default Wert für z. B. recordSchema wird vom
        # jeweiligen Server festgelegt;
        # also vorher ExplainFile anschauen!
        params = {
                # 'query': 'dog and cat and mouse',
                # 'queryType': 'cql',
                # default value is 1
                'startRecord': 1,

                # default value is determined by the server
                # for the sake of multi page browsing,
                # we use 10 as default, however
                'maximumRecords': 10,
                # 'recordSchema': 'mods',

                # 'record_XML_escaping' = True
                # resultSetTTL = True
                # Stylesheet = True
                # extension_parameters
                # sortKeys = True
                # facet_parameters
                # renderedBy = True
                # httpAccept = True
                # responseType = True
                # recordPacking = True
            }
        params.update(kwargs)

        if 'query' not in params.keys():
            raise KeyError("Request parameter 'query' must be set")

        return self.iterator(self, params)

    def explain(self):
        """Issue an Explain request to a SRU server.

        :rtype: :class:`srupy.models.Explain`
        """
        return Explain(self.harvest())

    def get_retry_after(self, http_response):
        """Docstring."""
        if http_response.status_code == 503:
            try:
                return int(http_response.headers.get('retry-after'))
            except TypeError:
                return self.default_retry_after
        return self.default_retry_after

    @staticmethod
    def _is_error_code(status_code):
        """Docstring."""
        return status_code >= 400
