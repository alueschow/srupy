# coding: utf-8
"""Collects classes for iterating over SRU responses.

:copyright: Copyright 2020 Andreas Lüschow
"""

from srupy import sruexceptions
from .models import (Record, EchoedRequest)


class BaseSRUIterator(object):
    """Iterator over SRU records.

    :param srupy: The SRUpy object that issued the first request.
    :type srupy: :class:`srupy.app.SRUpy`
    :param params: The SRU arguments.
    :type params:  dict
    """

    def __init__(self, srupy, params):
        """Docstring."""
        self.srupy = srupy
        self.params = params
        self._next_response()

    def __iter__(self):
        """Docstring."""
        return self

    def __next__(self):
        """Docstring."""
        return self.next()

    def _next_response(self):
        """Get the next response from the SRU server."""
        params = self.params
        self.sru_response = self.srupy.harvest(**params)
        # TODO
        error = self.sru_response.xml.find(
            './/' + self.srupy.sru_namespace + 'error')
        if error is not None:
            code = error.attrib.get('code', 'UNKNOWN')
            description = error.text or ''
            try:
                raise getattr(
                    sruexceptions, code[0].upper() + code[1:])(description)
            except AttributeError:
                raise sruexceptions.SRUError(description)

    def next(self):
        """Must be implemented by subclasses."""
        raise NotImplementedError


class SRUResponseIterator(BaseSRUIterator):
    """Handle SRU responses."""

    def __init__(self, srupy, params):
        """Docstring."""
        super(SRUResponseIterator, self).__init__(srupy, params)

        # get basic information
        self.number_of_records = int(self.sru_response.xml.find(
            './/' + self.srupy.sru_namespace + 'numberOfRecords').text)
        self.echo = EchoedRequest(self.sru_response.xml.find(
            './/' + self.srupy.sru_namespace + 'echoedSearchRetrieveRequest'))

        # handle Request parameters
        self._maximum_records = int(params.get('maximumRecords'))
        self._start_record = int(params.get('startRecord'))

    def _next_response(self):
        """Docstring."""
        super(SRUResponseIterator, self)._next_response()
        self._records = self.sru_response.xml.iterfind(
            './/' + self.srupy.sru_namespace + 'record')

    def next(self):
        """Return the next record."""
        while True:
            for r in self._records:
                return Record(r)
            self._handle_multiple_pages()
            self._next_response()

    def _handle_multiple_pages(self):
        """Get startRecord for next Request.

        (if not all available records were fetched)
        """
        if self._start_record + self._maximum_records < self.number_of_records:
            self._start_record += self._maximum_records
            self.params.update({
                'startRecord': self._start_record,
            })
        else:
            raise StopIteration
