#!/bin/env python
# -*- encoding: utf-8 -*-

"""Functionality handling user input in CLI."""

from __future__ import unicode_literals

import argparse
import re
import readline
import getpass
import requests

dateformats = ('(mon|tues|wednes|thurs|fri|satur|sun)day', 'tomorrow', 'today',
               'next month', 'next year', '[0-3]?[0-9]\. [a-z]{3,6}( \d{4})?',
               '\d+ (day|week|month|year)s?',
               )
timeformats = ('[0-1][0-9]:[0-5][0-9]',)


def parse_content(api, content):
    """Get labels, projects and date out of a content string.

    NOT as advanced as Todoist own parser. Does for instance not support
    white space in labels and projects.

    :rtype: list
    :return:
        The different parts that an item could consist of:

        1. The content, where the other parts have been stripped out.
        2. Project, if set. By it's project name, for now. Defaults to Inbox. #
           TODO: Change to project id!
        3. Date, if set. Only a limited format are accepted here, not all
           supported by Todoist.
        4. Labels, if set. Returned by its label names.
        5. Priority, in the range 1 (highest) to 4 (default, lowest).

    """
    content, project = parse_project(api, content)
    labelnames = set(l['name'].lower() for l in api.labels.all())
    content, labels = parse_labels(content, labelnames)
    content, date = parse_date(content)
    content, priority = parse_priority(content)

    # Remove superfluous spaces
    content = re.sub('  +', ' ', content).strip()
    return content, project, date, labels, priority


def parse_project(api, content):
    """Return first project found, and remove from content.

    TODO: Only support projects without space in its name, for now.

    """
    project = "Inbox"
    for p in re.findall('#(\w+)', content):
        try:
            api.get_projects_by_name(p)
        except Exception:
            continue
        else:
            content = content.replace('#' + p, '')
            return content, p
    return content, project


def parse_labels(content, labelnames):
    """Return labels found, and remove from content.

    :type labelnames: set
    :param labelnames:
        All labels' names, in lowercase. Used to only return valid labels.

    """
    labels = set(l for l in re.findall('\@(\w+)', content)
                 if l.lower() in labelnames)
    for l in labels:
        content = content.replace('@' + l, '')
    return content, labels


def parse_date(content):
    """Return first date format found, and remove from content"""
    for d in dateformats:
        m = re.search('({}( {})?)'.format(d, timeformats), content)
        if m:
            return content.replace(m.groups()[0], ''), m.groups()[0]
    return content, None


def parse_priority(content):
    # Find priority
    # Note: Frontend consider 1 highest, while the API consider 4 the highest.
    # In here, we have the frontend's perspective.
    priority = 4
    match = re.search("!!([1-4])", content)
    if match:
        priority = match.group(1)
        content = content.replace('!!{}'.format(priority), '')
    return content, priority


def login_dialog(api):
    """Authenticate user by asking for password."""
    while not api.token:
        print("Not authenticated with Todoist")
        mail = raw_input('E-mail address: ')
        pwd = getpass.getpass()
        try:
            api.user.login(mail, pwd)
        except requests.exceptions.HTTPError, e:
            if e.response.status_code not in (400, 401):
                raise
        else:
            if api.token:
                print("Authenticated!")
                return True
                # TODO: Add support for storing in .ini file (config)


def ask_confirmation(prompt, args=None):
    """Return True if user confirms prompt

    :type args: argparse.Namespace
    :param args:
        The parsed arguments from `argparse.ArgumentPaser`, to search for if
        the user has set `--assume-yes`, for less interaction.

    """
    if args and getattr(args, 'assume_yes'):
        return True
    ret = raw_input(unicode(prompt + u" (y/N): ").encode('utf8'))
    return ret == 'y'


def _set_completer(choices):
    """Setup a readline completer for tab completion of given choices.

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
        if regex_choices:
            if filter(lambda x: re.search(x, raw), choices):
                return raw
            print("Invalid {}, please try again (return ? for "
                  "overview)".format(category))
        else:
            if raw in choices:
                return raw
            raw = raw.lower()
            matches = filter(lambda x: raw in x.lower(), choices)
            if matches:
                ret = ask_choice_of_list("Please narrow it down:", matches)
                if ret is not None:
                    return matches[ret]
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


def ask_choice_of_list(prompt, choices, default=0):
    """Prompts user to select one choice by choosing a number.

    The user gets reprompted if invalid number. If users gives blank answer,
    the default is returned.

    :type prompt: str
    :param prompt: What to ask the user for, before the choices are printed.

    :rtype: int or None
    :return:
        The selected choice by its index number. Returns None if user aborted.

    """
    _set_completer(choices)
    while True:
        print(prompt)
        for i, choice in enumerate(choices):
            print("  {}: {}".format(i+1, choice))
        raw = raw_input("Please choose 1-{} [{}]: ".format(len(choices),
                                                           default+1))
        if not raw:
            return default
        raw = raw.strip()
        try:
            choice = int(raw.strip())
        except ValueError:
            if raw == 'a':
                return None
            raw = raw_input("Invalid number, choose 1-{}: ".format(
                                                        len(choices)))
            raw = raw.strip()
            try:
                choice = int(raw)
            except ValueError:
                if raw == 'a':
                    return None
                print("Invalid number")
                continue

        if choice < 1 or choice > len(choices):
            print("Number not in range, please try again")
            continue
        return choice - 1


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
    p.add_argument('--assume-yes', help="Assume yes on non-critical decisions")
    return p
