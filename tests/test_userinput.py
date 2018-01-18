#!/bin/env python
# -*- encoding: utf-8 -*-

""" Testing functionality for user input (CLI)."""

from __future__ import unicode_literals

from todoist_gtd_utils import userinput

latest_response = 'something'


def raw_input2(prompt):
    """Mock raw_input"""
    return latest_response.encode('utf-8')


# Mock stdin:
userinput.raw_input2 = raw_input2


def test_internal_raw_input():
    """Just testing that the test works…"""
    global latest_response
    latest_response = "reÆØÅponße"
    ret = raw_input2('¡→ij2o3ijv 23klj')
    assert ret.decode('utf-8') == latest_response


def test_parse_raw_input():
    global latest_response
    latest_response = "response"
    ret = userinput.get_input("test")
    assert ret == latest_response


def test_parse_raw_input_unicode():
    global latest_response
    latest_response = "reÆØÅponße"
    ret = userinput.get_input("ÆØÅtest ¡ĸ»$¡¡£$¡")
    assert ret == latest_response


def test_parse_simple_content():
    pass
    # for input in ('', 'test', 'longer test', 'abc 123 a2 a-z 0-9 _ + *'):
    #     result = userinput.parse_content(None, input)
    #     assert input == result[0]


def test_parse_content():
    # TODO: need to mock the api object first!
    pass


def test_parse_dates():
    for (input, exp_content, exp_date) in (
            ('', '', None),
            ('today', '', 'today'),
            ('This after 2 days', 'This', 'after 2 days'),
            ('every monday', '', 'every monday'),
            ('Not after 10 days', 'Not', 'after 10 days'),
            ('What is 10 days this?', 'What is this?', '10 days'),
            ('every workday do something', 'do something', 'every workday'),
            ('This is 1. may', 'This is', '1. may')):
        content, date = userinput.parse_date(input)
        assert exp_content == content
        assert exp_date == date
