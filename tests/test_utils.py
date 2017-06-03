#!/bin/env python
# -*- encoding: utf-8 -*-

""" Testing utility functionality."""

from __future__ import unicode_literals

from todoist_gtd_utils import utils



def test_prioriy_conversion():
    for (input, api_pri) in ((1, 4), (2, 3), (3, 2), (4, 1)):
        assert utils.frontend_priority_to_api(input) == api_pri


def test_prioriy_as_string():
    for (input, api_pri) in (('1', 4), ('2', 3), ('3', 2), ('4', 1)):
        assert utils.frontend_priority_to_api(input) == api_pri
