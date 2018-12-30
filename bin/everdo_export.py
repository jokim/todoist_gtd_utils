#!/bin/env python
# -*- encoding: utf-8 -*-

""" Output Todoist data to JSON file for Everdo.

See https://everdo.net for the Everdo application.

See https://forum.everdo.net/t/import-data-format/106/3 for data format.

Most of my business policies are hardcoded in here. Could most likely be
somewhat configurable, but hey, this is hopefully a oneshot migration.

Some simplifications:

- Everdo has a flat project structure, in contrast to Todoists 4 levels. Top
  level becomes Area, but the rest are included as their own projects. Some
  cleanup might be needed after import.

- Colors from Todoist are ignored.

- Dates for creation and update are ignored.

"""

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import sys
import time

from todoist_gtd_utils import TodoistGTD
from todoist_gtd_utils import everdo
from todoist_gtd_utils import userinput
from todoist_gtd_utils import utils


def add_tags(edo, api):
    i = 0
    for label in api.labels.all():
        tag_type = 'l'
        title = label['name']
        if label['color'] == 9:
            tag_type = 'c'
        if label['color'] == 0:
            # Everdo handles Contexts somewhat special:
            title = '@' + title
        edo.add_tag(everdo.Everdo_Tag(tag_type, title), label)
        i += 1
    print("Added %d tags" % i)


def add_inbox(edo, api):
    i = 0
    p = api.get_project_by_name('Inbox')
    for item in p.get_child_items():
        add_item(edo, api, item)
        i += 1
    print("Added %d items from Inbox" % i)


def add_active_projects(edo, api):
    added_projects = 0
    added_items = 0
    added_standalone_items = 0
    for t in api.get_targetprojects():
        # The target projects are my "areas" in Everdo (first guess)
        area = everdo.Everdo_Tag('a', t['name'])
        edo.add_tag(area, t)

        for p in t.get_child_projects():
            if p['is_deleted']:
                continue
            completed_on = None
            if p['is_archived']:
                completed_on = int(time.time())
            eproject = everdo.Everdo_Project(
                    'a', p['name'], is_focused=p['is_favorite'],
                    completed_on=completed_on)
            edo.add_item(eproject, p)
            added_projects += 1

            for item in p.get_child_items():
                add_item(edo, api, item, parent=eproject)
                added_items += 1

        for item in t.get_child_items():
            add_item(edo, api, item, parent=None)
            added_standalone_items += 1

    print("Added %d active projects, with %d items" % (added_projects,
                                                       added_items))
    print("Added %d standalone items" % added_standalone_items)


def add_item(edo, api, item, list_type=None, parent=None):
    """Add an action/item (not project)"""
    # TODO: add policies
    # - Someday?
    # - If item is only a comment, include it in the projects
    #   comment?
    completed_on = due_date = None

    if not list_type:
        list_type = 'a'
        if item.is_waiting():
            list_type = 'w'
    # TODO: verify if list_type is set correctly
    if item['is_archived'] or item['date_completed']:
        list_type = 'r'
        completed_on = int(time.time())
        if 'date_completed' in item.data:
            completed_on = everdo.duedateutc2stamp(item['date_completed'])
    if item['due_date_utc']:
        date = utils.parse_utc_to_datetime(item['due_date_utc'])
        due_date = everdo.datetime2stamp(date)
    if item['date_string'] and not item['due_date_utc']:
        print("WARN: due date mismatch?")
        print(" due_date_utc: %s" % item['due_date_utc'])
        print(" date_string: %s" % item['date_string'])
        print("Okay to only care about 'due_date_utc'?")
        print()

    tags = [edo.get_eid(l) for l in item['labels']]

    # TODO:
    # - add api.notes.all for item to note? summary? ask?
    #
    # TODO: Should handle item.is_title(), but don't know where to put it

    # TODO: Support converting date_added and date_completed
    ret = everdo.Everdo_Action(parent,
                               list_type=list_type,
                               title=item['content'],
                               completed_on=completed_on,
                               due_date=due_date,
                               tags=tags)
    edo.add_item(ret, item)
    return ret


def add_someday(edo, api):
    # TODO
    for p in api.get_somedaymaybe():
        pass


def main():
    p = userinput.get_argparser(
            description="Export Todoist data to file for Everdo")
    # p.add_argument('--export-cache', type.
    # p.add_argument('--import-cache', type.
    p.add_argument("out", default=sys.stdout, type=argparse.FileType('w'),
                   help="JSON output file, for Everdo")
    args = p.parse_args()
    api = TodoistGTD(configfiles=args.configfile, token=args.token)
    if not api.is_authenticated():
        userinput.login_dialog(api)
    print("Full sync with Todoist first…")
    # TODO: add back when done testing
    # api.fullsync()
    print("Full sync done")

    edo = everdo.Everdo_File()
    add_tags(edo, api)
    add_inbox(edo, api)
    add_active_projects(edo, api)
    add_someday(edo, api)
    # TODO: more?
    edo.export(args.out)
    print("Exported %d items and %d tags" % (len(edo.items), len(edo.tags)))
    args.out.close()


if __name__ == '__main__':
    main()
