#!/bin/env python
# -*- encoding: utf-8 -*-

"""Utility functions for utility project."""

import argparse
import re


def ask_confirmation(prompt, interactive=True):
    """Return True if user confirms prompt"""
    if not interactive:
        return True
    ret = raw_input(unicode(prompt + u" (y/N): ").encode('utf8'))
    return ret == 'y'


def ask_choice(prompt, choices, default=None, category='choice',
               regex_choices=False):
    """Prompts user to select one choice.

    The user gets reprompted if invalid choice. If users gives blank answer,
    the default is returned. Note that "?" is reserved, as the user then gets
    the whole list of choices.

    :type prompt: str
    :param prompt: What to ask the user for. Result: `Prompt [default]: `

    :type regex_choices: bool
    :param regex_choices:
        True the choices are regexes to be matched. False means the choice must
        match exactly one of the strings in `choices`.

    """
    while True:
        raw = raw_input("{} [{}]: ".format(prompt, default))
        if not raw:
            return default
        if raw == '?':
            print u'Choices: {}'.format(u', '.join(choices))
            continue
        raw = raw.strip()
        if not regex_choices:
            if raw in choices:
                return raw
        else:
            if filter(lambda x: re.search(x, raw), choices):
                return raw
        print ("Invalid {}, please try again (return ? for "
               "overview)".format(category))


def ask_multichoice(prompt, choices, default=[], category='choice',
                    separator=' '):
    """Prompts user to select one or many out of given choices.

    The user gets reprompted if invalid choice. If users gives blank answer,
    the default is returned. Note that "?" is reserved, as the user then gets
    the whole list of choices.

    :type prompt: str
    :param prompt: What to ask the user for. Result: `Prompt [default]: `

    """
    while True:
        raw = raw_input("{} [Default: {}]: ".format(prompt,
                                                    separator.join(default)))
        if not raw:
            return default
        if raw == '?':
            print u'Choices: {}'.format(', '.join(choices))
            continue
        raw = raw.strip()
        selections = raw.split(separator)
        invalid_selections = filter(lambda x: x not in choices, selections)
        if not invalid_selections:
            return selections
        print "Invalid {}: {}".format(category,
                                      separator.join(invalid_selections))
        print "(return ? for overview)"


def get_argparser(*args, **kwargs):
    """Init an argparser with default functionality"""
    p = argparse.ArgumentParser(*args, **kwargs)
    p.add_argument('--configfile', help="Change path to config file",
                   default='~/.todoist_gtd_utils.ini')
    p.add_argument('--token', help="API token to user for user")
    return p
