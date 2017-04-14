#!/bin/env python
# -*- encoding: utf-8 -*-

"""Utility functions for utility project."""

from __future__ import print_function

import argparse
import re
import readline


def ask_confirmation(prompt, interactive=True):
    """Return True if user confirms prompt"""
    if not interactive:
        return True
    ret = raw_input(unicode(prompt + u" (y/N): ").encode('utf8'))
    return ret == 'y'


def _set_completer(choices):
    """Return a readline completer for tab completion of given choices.

    Usable for quicker input of e.g. labels and projects.

    """
    choices = sorted(choices)

    # Stolen from
    # http://stackoverflow.com/questions/187621/how-to-make-a-python-command-line-program-autocomplete-arbitrary-things-not-int
    def completer(text, state):
        options = [c for c in choices if c.startswith(text)]
        try:
            return options[state]
        except IndexError:
            return None

    readline.set_completer(completer)
    readline.parse_and_bind('tab: complete')


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
    _set_completer(choices)
    while True:
        raw = raw_input("{} [{}]: ".format(prompt, default))
        if not raw:
            return default
        if raw == '?':
            present_choices(choices)
            continue
        raw = raw.strip()
        if not regex_choices:
            if raw in choices:
                return raw
        else:
            if filter(lambda x: re.search(x, raw), choices):
                return raw
        print("Invalid {}, please try again (return ? for "
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
    _set_completer(choices)
    while True:
        raw = raw_input("{} [Default: {}]: ".format(prompt,
                                                    separator.join(default)))
        if not raw:
            return default
        if raw == '?':
            present_choices(choices)
            continue
        raw = raw.strip()
        selections = raw.split(separator)
        invalid_selections = filter(lambda x: x not in choices, selections)
        if not invalid_selections:
            return selections
        print("Invalid {}: {}".format(category,
                                      separator.join(invalid_selections)))
        print("(return ? for overview)")


def present_choices(choices):
    """Print out given choices.

    Length of choices defines how they are presented (space or newline).

    """
    max_choice_length = max(choices, key=len)
    has_spaces = any(' ' in c for c in choices)
    if max_choice_length > 50 or has_spaces:
        print(u'Choices:\n{}'.format('\n'.join(sorted(choices))))
    else:
        print(u'Choices: {}'.format(', '.join(sorted(choices))))


def get_argparser(*args, **kwargs):
    """Init an argparser with default functionality"""
    p = argparse.ArgumentParser(*args, **kwargs)
    p.add_argument('--configfile', help="Change path to config file",
                   default='~/.todoist_gtd_utils.ini')
    p.add_argument('--token', help="API token to user for user")
    return p


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
