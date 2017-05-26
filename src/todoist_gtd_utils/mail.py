#!/bin/env python
# -*- encoding: utf-8 -*-

"""Functionality for handling mails for our usage.

This is mainly being able to parse and present them in a readable manner, in
Todoist.

"""

from __future__ import unicode_literals

import email
import email.header

from todoist_gtd_utils import utils


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
            ' '.join(unicode(t[0], t[1] or 'latin1') for t in
                     email.header.decode_header(raw)))

    def get_body(self):
        # TODO: support encoding
        if self.mail.is_multipart():
            # TODO: Filter html etc
            return '\n'.join(p.get_payload(decode=True) for p in
                             self.mail.get_payload() if p)
        else:
            return unicode(self.mail.get_payload(decode=True),
                           self.mail.get_content_charset() or
                           self.default_encoding)

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
