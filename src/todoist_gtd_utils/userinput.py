#!/bin/env python
# -*- encoding: utf-8 -*-

"""Functionality handling user input in CLI."""

from __future__ import unicode_literals

import os
import argparse
import re
import readline
import getpass
import requests

from .utils import trim_whitespace, frontend_priority_to_api

dateformats = ('(after |every )?(mon|tues|wednes|thurs|fri|satur|sun)day',
               '(after |every )?tomorrow',
               'today',
               '(after |every )?(\d+ )?(work)?day(s)?',
               '(after |every )?next month', '(after |every )?next year',
               '[0-3]?[0-9]\. [a-z]{3,6}( \d{4})?',
               'in \d+ (day|week|month|year)s?',
               )
timeformats = ('[0-1][0-9]:[0-5][0-9]',)


# For mocking/testing behaviour
raw_input2 = raw_input


def get_input(prompt):
    """Unicodify raw_input"""
    # Force unicodified input
    assert isinstance(prompt, unicode)
    # TODO: How to check terminals' charset? LC_ALL?
    return unicode(raw_input2(prompt.encode('utf-8')), 'utf-8')


def dialog_new_item(api, name=None, project=None):
    """Ask for all input needed to create a new item.

    :type api: TodoistGTD

    :type name: unicode
    :param name: The given description of item. User gets asked if not given.

    :type project: todoist.model.Project
    :param project:
        Sets a default project. The use case is when in a menu for a given
        project, it makes sense to default to that project.

    :rtype: todoist.model.Item
    :return: The created item, using the Todoist API.

    """
    if not name:
        name = get_input("Name of action: ")
    content, parsed_input = parse_item_content(api, name)
    # TODO: Print and colorize invalid project and label names (# and @), to
    # highlight what looks like typos?

    if parsed_input['project']:
        project = parsed_input['project']

    projects = dict((p['id'], unicode(p['name'])) for p in api.projects.all())
    project = ask_choice('Project', choices=projects, default=project['id'],
                         category="project")
    all_labels = dict((l['id'], unicode(l['name']).lower()) for l in
                      api.labels.all())
    labels = ask_multichoice('Labels', choices=all_labels,
                             default=parsed_input['labels'], category="labels")
    date = ask_choice('Date', choices=dateformats,
                      default=parsed_input['date'], category="date",
                      regex_choices=True)
    priority = ask_choice('Priority', choices=[1, 2, 3, 4],
                          default=parsed_input['priority'],
                          category="priority")
    api_pri = frontend_priority_to_api(priority)

    # TODO: handle go back in menu etc?

    item = api.items.add(content + ' :email:.', priority=api_pri, indent=1,
                         project_id=project, date_string=date, labels=labels)
    return item


def ask_labels(api, default):
    """Make user choose labels.

    TODO: Support creating a new label?

    """


def ask_date(api, default):
    """Make user choose a relative or absolute date"""


def ask_priority(api, default):
    """Make user choose a prioritiy."""


def ask_description(api, default):
    """Ask user for a description, with a default value"""
    ret = get_input("Set description [{}]: ".format(default))
    if not ret:
        return default
    return ret


def parse_item_content(api, content):
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
    content, labels = parse_labels(api, content)
    content, date = parse_date(content)
    content, priority = parse_priority(content)

    # Remove superfluous spaces
    content = re.sub('  +', ' ', content).strip()
    return content, {'project': project, 'date': date, 'labels': labels,
                     'priority': priority}


def parse_project(api, content):
    """Return first project found, and remove from content.

    TODO: Only support projects without space in its name, for now.

    :rtype: tuple
    :return:
        Tuple with three elements: New content, project name and TodoistProject
        (elns). If no project was found, the last two elements are None, and
        the first is unmodified.

    """
    for p in re.findall('#(\w+)', content):
        try:
            p_obj = api.get_projects_by_name(p)
        except Exception:
            # TODO: more granular exception
            continue
        else:
            content = content.replace('#' + p, '')
            return content, p_obj
    return content, None


def parse_labels(api, content):
    """Return labels found, and remove from content"""
    found_labels = []
    for label in api.labels.all():
        labelname = '@{}'.format(label['name'])
        # TODO: support lowercase (need to use `re` then, to modify)
        if labelname in content:
            found_labels.append(label)
            content = content.replace(labelname, '')
    return content, found_labels


def parse_date(content):
    """Return first date format found, and remove from content"""
    for d in dateformats:
        m = re.search('({}( {})?)'.format(d, timeformats), content)
        if m:
            return (trim_whitespace(content.replace(m.groups()[0], '')),
                    trim_whitespace(m.groups()[0]))
    return content, None


def parse_priority(content):
    # Find priority
    # Note: Frontend consider 1 highest, while the API consider 4 the highest.
    # In here, we have the frontend's perspective.
    priority = 4
    match = re.search("!!([1-4])", content)
    if match:
        priority = int(match.group(1))
        content = content.replace('!!{}'.format(priority), '')
    return content, priority


def login_dialog(api):
    """Authenticate user by asking for password."""
    while not api.token:
        print("Not authenticated with Todoist")
        mail = get_input('E-mail address: ')
        pwd = getpass.getpass()
        try:
            api.user.login(mail, pwd)
        except requests.exceptions.HTTPError as e:
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
    if args and getattr(args, 'yes'):
        return True
    ret = get_input(prompt + " (y/N): ")
    return ret == 'y'


def _set_completer(choices):
    """Setup a readline completer for tab completion of given choices.

    Usable for quicker input of e.g. labels and projects.

    :type choices: list, tuple or dict
    :param choices: If a dict, only its keys are used.

    """
    if isinstance(choices, dict):
        choices = choices.keys()
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


def ask_choice(prompt, choices, default='', category='choice',
               regex_choices=False):
    """Prompts user to select one of given choices.

    Warning: Choices can't have same value.

    The user gets reprompted if invalid choice. If users gives blank answer,
    the `default` is returned. Note that "?" is reserved, as the user then gets
    the whole list of choices.

    :type prompt: unicode
    :param prompt: What to ask the user for. Result: `Prompt [default]: `

    :type choices: list, tuple or dict
    :param choices:
        The options the user are limited to select. If a dict, the values are
        what the user sees and selects from, while the chosen *key* is
        returned.

    :param default:
        What to return if none is selected. If choices are a dict, the default
        value must be a valid *key*, otherwize an error is raised.

    :type regex_choices: bool
    :param regex_choices:
        If set to True the choices are regexes to be matched. False means the
        choice must match exactly one of the strings in `choices`.

    """
    mapping = values = None
    default_value = default

    if isinstance(choices, dict):
        # Invert dict, to find keys to return later:
        mapping = dict((unicode(v), k) for k, v in choices.iteritems())
        values = map(unicode, choices.values())
        default_value = choices.get(default, '')
    else:
        values = choices

    if default and default not in choices:
        raise Exception("Default value {!r} missing from input"
                        .format(default))

    def get_return(input):
        if mapping:
            return mapping[input]
        return input

    _set_completer(values)
    while True:
        raw = get_input(("{} [{}]: ".format(prompt, default_value)))
        if not raw:
            return default
        if raw == '?':
            present_choices(values)
            continue
        raw = raw.strip()
        if regex_choices:
            if filter(lambda x: re.search(x, raw), values):
                return raw
            print("Invalid {}, please try again (? for overview)"
                  .format(category))
        else:
            if raw in values:
                return get_return(raw)
            raw = raw.lower()
            matches = filter(lambda x: raw in x.lower(), values)
            if matches:
                try:
                    ret = ask_choice_of_list("Narrow down (CTRL+D to cancel):",
                                             matches)
                except EOFError:
                    # user wants to reset
                    print("Ok, cancel")
                    continue
                if ret is not None:
                    return get_return(matches[ret])
        print("Invalid {}, please try again (? for overview)"
              .format(category))


def ask_multichoice(prompt, choices, default=[], category='choice',
                    separator=' '):
    """Prompts user to select one or many out of given choices.

    The user gets reprompted if invalid choice. If users gives blank answer,
    the default is returned. Note that "?" is reserved, as the user then gets
    the whole list of choices.

    :type prompt: str
    :param prompt: What to ask the user for. Result: `Prompt [default]: `

    :type choices: list, tuple or dict
    :param choices:
        The choices the user could select from. If dict, the user choose one of
        the values while the key is returned.

        Note: Values (and keys) must be unique to be selected.

    """
    mapping = None
    default_value = default

    if isinstance(choices, dict):
        # Invert dict, to find keys to return later:
        mapping = dict((unicode(v), k) for k, v in choices.iteritems())
        values = map(unicode, choices.values())
        default_values = [unicode(choices.get(d)) for d in default]
    else:
        values = choices
        default_values = default

    # TODO: assert that default is amongst choices

    _set_completer(values)

    def get_return(input):
        if mapping:
            return [mapping[i] for i in input]
        return input

    while True:
        question = "{} [Default: {}]: ".format(prompt,
                                               separator.join(default_values))
        raw = get_input(question)
        if not raw:
            return default
        if raw == '?':
            present_choices(values)
            continue
        raw = raw.strip()
        selections = raw.split(separator)
        print("Availbale values: {}".format(values))
        print("Input separated: {}".format(selections))
        invalid_selections = filter(lambda x: x not in values, selections)
        if not invalid_selections:
            return get_return(selections)
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
    if len(choices) < 1:
        raise Exception("No choices to choose from")
    _set_completer(choices)
    while True:
        print(prompt)
        for i, choice in enumerate(choices):
            print("  {}: {}".format(i+1, choice))
        raw = get_input("Please choose 1-{} [{}]: ".format(len(choices),
                                                           default+1))
        if not raw:
            return default
        raw = raw.strip()
        try:
            choice = int(raw.strip())
        except ValueError:
            if raw == 'a':
                return None
            raw = get_input("Invalid number, choose 1-{}: ".format(
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


def ask_menu(options, prompt="Choose", quit_char='q'):
    """Simple menu loop executing given callbacks according to user input.

    :type options: dict
    :param options:
        What the user can choose from. The keys are the char to input for
        selection, and the values are a two element list with an explanation
        and a callback. Example::

            {'q': ('Quit', sys.exit), 'e': ('Edit', ask_edit), }

        Note: The char '?' is reserved.

        TODO: Should the callback's return have something to say?

    :type prompt: str
    :param prompt: What to ask for in the menu

    """
    _set_completer(options)
    while True:
        try:
            answer = get_input("{} (? for menu): ".format(prompt))
        except EOFError:
            print("Ok")
            return
        answer = answer.strip()
        if answer == '?':
            print("Options: ")
            for k in sorted(options):
                print("{}: {}".format(k, options[k][0]))
            print("q: Quit this menu (go next)")
            print("?: Show this info")
            print('')
        elif answer == quit_char:
            print("Ok")
            return
        elif answer in options:
            try:
                # Run callback
                options[answer][1]()
                print('')
            except EOFError:
                print("Command aborted")
        else:
            print("Invalid option: {}".format(answer))
            print("(Input ? for list of options)")


def present_choices(choices):
    """Print out given choices.

    Length of choices defines how they are presented (space or newline).

    If choices are a dict, only its keys are used.

    """
    if isinstance(choices, dict):
        choices = choices.keys()
    max_choice_length = max(choices, key=len)
    has_spaces = any(' ' in c for c in choices)
    if max_choice_length > 50 or has_spaces:
        print('Choices:\n{}'.format('\n'.join(sorted(choices))))
    else:
        print('Choices: {}'.format(', '.join(sorted(choices))))


def get_argparser(*args, **kwargs):
    """Init an argparser with default functionality"""
    p = argparse.ArgumentParser(*args, **kwargs)
    p.add_argument('--configfile', help="Change path to config file",
                   default='~/.todoist_gtd_utils.ini')
    p.add_argument('--token', help="API token to user for user")
    p.add_argument('--yes', action='store_true',
                   help="Assume yes on non-critical decisions")
    return p


def get_terminal_size():
    """Return the terminal size, in number of characters"""
    # https://stackoverflow.com/questions/566746/how-to-get-linux-console-window-width-in-python
    rows, columns = os.popen('stty size', 'r').read().split()
    return int(rows), int(columns)
