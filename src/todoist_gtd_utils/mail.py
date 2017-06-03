#!/bin/env python
# -*- encoding: utf-8 -*-

"""Functionality for handling mails for our usage.

This is mainly being able to parse and present them in a readable manner, in
Todoist.

"""

from __future__ import unicode_literals

import email
import email.header
from quopri import ishex
from quopri import unhex

from todoist_gtd_utils import utils
from todoist_gtd_utils.utils import to_unicode
import todoist_gtd_utils.mail


class SimpleMailParser(object):
    """Handling a given mail, by parsing and presenting its data.

    Data is returned in Unicode.

    """
    default_encoding = 'latin1'

    def __init__(self, mailfile):
        self.mail = email.message_from_file(mailfile)

    def get_header(self, key):
        """Return a mail's header, unicodified."""
        raw = self.mail.get(key)
        if not raw:
            return raw
        return utils.trim_whitespace(
            ' '.join(to_unicode(t[0], t[1] or 'latin1', 'replace') for t in
                     email.header.decode_header(raw)))

    def get_decoded_payload(self, p):
        """Try to return a unicodified payload.

        Should accept badly encoded data without failing.

        """
        charset = p.get_content_charset() or self.default_encoding
        try:
            return to_unicode(p.get_payload(decode=True), charset, 'replace')
        except UnicodeEncodeError:
            load = to_unicode(p.get_payload(decode=False), charset, 'replace')
            cte = self.mail.get('content-transfer-encoding', '').lower()
            if cte == 'quoted-printable':
                return todoist_gtd_utils.mail.decode_quoted_printable(load,
                                                                      header=0)
            return load

    def get_body(self):
        # TODO: support encoding
        if self.mail.is_multipart():
            # TODO: Filter html etc
            return '\n'.join(self.get_decoded_payload(p) for p in
                             self.mail.get_payload())
        else:
            return self.get_decoded_payload(self.mail)

    def get_presentation(self, *args, **kwargs):
        """Return a presentable formatted mail.

        Each *args argument could be prefixed with:

        * = The header and its value should be marked with **bold**
        _ = The header should be ignored if no value

        """
        body = kwargs.get('body', True)
        lines = []
        for key in args:
            bold = optional = False
            if key.startswith('*'):
                key = key[1:]
                bold = True
            if key.startswith('_'):
                key = key[1:]
                optional = True

            value = self.get_header(key)
            if optional and not value:
                continue
            if bold:
                lines.append('**{}: {}**'.format(key, value))
            else:
                lines.append('{}: {}'.format(key, value))
        if body:
            lines.append('')
            lines.append(self.get_body())
        return '\n'.join(lines)


def decode_quoted_printable(input, header=0, encoding='utf-8'):
    """As quopri.decodestring, but with Unicode support.

    This is mainly a copy quopri.decodestring, slightly rewritten just to
    support unicode, and in a hackish way!

    TODO: Are there libraries that support this in unicode to rely on instead?

    """
    ESCAPE = '='
    ret = []
    new = bytearray()
    for line in input.split('\n'):
        if not line:
            # TODO: wat?
            break
        i = 0
        n = len(line)
        if line.endswith('\n'):
            partial = 0
            n = n-1
            # Strip trailing whitespace
            while n > 0 and line[n-1] in " \t\r":
                n = n-1
        else:
            partial = 1

        while i < n:
            c = line[i]
            if c == '_' and header:
                new += bytearray(' ', encoding)
                i = i+1
            elif c != ESCAPE:
                new += bytearray(c, encoding)
                i = i+1
            elif i+1 == n and not partial:
                partial = 1
                break
            elif i+1 < n and line[i+1] == ESCAPE:
                new += bytearray(ESCAPE, encoding)
                i = i+2
            elif i+2 < n and ishex(line[i+1]) and ishex(line[i+2]):
                new.append(unhex(line[i+1:i+3]))
                i = i+3
            else:
                # Bad escape sequence -- leave it in
                new += bytearray(c, encoding)
                i = i+1
        if not partial:
            ret.append(new.decode(encoding))
            new = bytearray()
    if new:
        ret.append(new.decode(encoding))
    return '\n'.join(ret)
