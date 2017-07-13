#!/bin/env python
# -*- encoding: utf-8 -*-

""" Testing functionality for user input (CLI)."""

from todoist_gtd_utils import userinput


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
