#!/bin/env python
# -*- encoding: utf-8 -*-

""" Testing utility functionality."""

from __future__ import unicode_literals

from todoist_gtd_utils import utils


def test_decode_quoted_printable():
    tests = (("hei og hopp", "hei og hopp"),
             ("hei =C3=A5 hopp", "hei å hopp"),
             ("hei_=C3=A5_hopp", "hei_å_hopp"),
             )
    for test, answer in tests:
        ret = utils.decode_quoted_printable(test)
        assert ret == answer


def test_decode_quoted_printable_latin1():
    tests = (("hei og hopp", "hei og hopp"),
             ("hei =E5 hopp", "hei å hopp"),
             ("hei_=E5_hopp", "hei_å_hopp"),
             )
    for test, answer in tests:
        ret = utils.decode_quoted_printable(test, False, 'latin-1')
        assert ret == answer


def test_decode_quoted_printable_headers():
    tests = (("hei og_hopp", "hei og hopp"),
             ("hei =C3=A5 hopp", "hei å hopp"),
             ("hei_=C3=A5_hopp", "hei å hopp"),
             )
    for test, answer in tests:
        ret = utils.decode_quoted_printable(test, True)
        assert ret == answer


def test_prioriy_conversion():
    for (input, api_pri) in ((1, 4), (2, 3), (3, 2), (4, 1)):
        assert utils.frontend_priority_to_api(input) == api_pri


def test_prioriy_as_string():
    for (input, api_pri) in (('1', 4), ('2', 3), ('3', 2), ('4', 1)):
        assert utils.frontend_priority_to_api(input) == api_pri
