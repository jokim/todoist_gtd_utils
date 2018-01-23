#!/bin/env python
# -*- encoding: utf-8 -*-

"""Utility functions for utility project."""

from __future__ import unicode_literals
from __future__ import print_function

import re
import datetime


def to_unicode(input, encoding, errors):
    """Shortcut for decoding to unicode"""
    if isinstance(input, unicode):
        return input
    if input is None:
        return input
    return unicode(input, encoding, errors)


def trim_whitespace(txt):
    """Remove double whitespace"""
    return re.sub('[\ \t]+', ' ', txt.strip())


def trim_too_long(txt, size=30, suffix=u'…'):
    """Shorten sentence, and add a suffix if too long.

    :type txt: unicode or str
    :param txt: The text to shorten

    :type size: int
    :param size: The length of result, including suffix

    """
    if len(txt) <= size:
        return txt
    return txt[:size-len(suffix)].rstrip() + suffix


def frontend_priority_to_api(pri):
    """Return the priority as the API considers it."""
    try:
        pri = int(pri)
    except ValueError:
        return 1
    if pri == 1:
        return 4
    if pri == 2:
        return 3
    if pri == 3:
        return 2
    return 1


def parse_utc_to_datetime(datestring):
    """Todoist includes due dates in a verbose format that needs to be parsed.

    Examples:

        u'Wed 03 Mar 2021 22:59:59 +0000'

    """
    d = datetime.datetime.strptime(datestring, '%a %d %b %Y %H:%M:%S +0000')
    # TODO: Is this always correct, or does datetime convert to local time?
    return d
