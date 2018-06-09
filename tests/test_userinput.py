#!/bin/env python
# -*- encoding: utf-8 -*-

""" Testing functionality for user input (CLI)."""

from __future__ import unicode_literals

from todoist_gtd_utils import userinput

_latest_responses = []


def add_response(input):
    """Feed user input"""
    global _latest_responses
    _latest_responses.append(unicode(input))


def raw_input2(prompt):
    """Mock raw_input"""
    print(prompt)
    global _latest_responses
    last_response = _latest_responses.pop(0)
    return last_response.encode('utf-8')


# Mock stdin:
userinput.raw_input2 = raw_input2


def test_internal_raw_input():
    """Just testing that the test works…"""
    response = "reÆØÅponße"
    add_response(response)
    ret = raw_input2('¡→ij2o3ijv 23klj')
    assert ret.decode('utf-8') == response


def test_parse_raw_input():
    response = "response"
    add_response(response)
    ret = userinput.get_input("test")
    assert ret == response


def test_parse_raw_input_unicode():
    response = "reÆØÅponße"
    add_response(response)
    ret = userinput.get_input("ÆØÅtest ¡ĸ»$¡¡£$¡")
    assert ret == response


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


def test_ask_choice_simple():
    add_response("abc")
    answer = userinput.ask_choice(prompt="Enter data:", choices=['abc', 'def'])
    assert answer == 0


def test_ask_choice_default():
    add_response("")
    answer = userinput.ask_choice(prompt="Enter data:", choices=['abc', 'def'],
                                  default=1)
    assert answer == 1


def test_ask_choice_dict():
    add_response("second")
    answer = userinput.ask_choice(prompt="",
                                  choices={1: 'first', 'abc': 'second'})
    assert answer == 'abc'


def test_ask_choice_dict_default():
    add_response("")
    default = 'ro98989ar'
    answer = userinput.ask_choice(prompt="",
                                  choices={'bob': 'Bob Johnson',
                                           'mary': 'Mary Bee', },
                                  default=default)
    assert answer == default


def test_ask_multichoice_simple():
    add_response('abc ghi')
    answer = userinput.ask_multichoice(prompt="Enter data:",
                                       choices=['abc', 'def', 'ghi', 'other'])
    assert answer == [0, 2]


def test_ask_multichoice_default():
    add_response('')
    answer = userinput.ask_multichoice(prompt="Enter data:",
                                       default=['ghi', 'other'],
                                       choices=['abc', 'def', 'ghi', 'other'])
    assert answer == ['ghi', 'other']


def test_ask_multichoice_dict():
    add_response('12 14')
    answer = userinput.ask_multichoice(
                            prompt="Enter data:",
                            choices={'abc': 12, 'def': 13, 'ghi': 14})
    assert answer == ['abc', 'ghi']


def test_ask_multichoice_dict_default():
    add_response('')
    answer = userinput.ask_multichoice(
        prompt="Enter data:", choices={'abc': 12, 'def': 13, 'ghi': 14},
        default=['def', 'ghi'])
    assert answer == ['def', 'ghi']


def test_ask_filter_regex():
    add_response('')
    answer = userinput.ask_filter("Age", '\d+', default='100')
    assert answer == '100'
    add_response('23')
    answer = userinput.ask_filter("Age", '\d+', default='100')
    assert answer == '23'
    add_response('18')
    answer = userinput.ask_filter("Age", ['\d+', '\w+'])
    assert answer == '18'
    add_response('abc')
    answer = userinput.ask_filter("Age or chars", ['\d+', '\w+'], default='0')
    assert answer == 'abc'
