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
import re
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
        add_item(edo, api, item, list_type='i')
        i += 1
    print("Added %d items from Inbox" % i)


def add_active_projects(edo, api):
    added_projects = 0
    added_items = 0
    added_standalone_items = 0
    for t in api.get_targetprojects():
        # The target projects are my "areas" in Everdo (first guess)
        area = everdo.Everdo_Tag('a', t['name'])
        # edo.add_tag(area, t)
        edo.tags.append(area)

        for p in t.get_child_projects():
            if p['is_deleted']:
                continue
            completed_on = None
            if p['is_archived']:
                completed_on = int(time.time())
            eproject = everdo.Everdo_Project(
                    'a', p['name'], is_focused=p['is_favorite'],
                    completed_on=completed_on, tags=[area.data['id']])
            edo.add_item(eproject, p)
            added_projects += 1

            for item in p.get_child_items():
                if item['is_deleted']:
                    continue
                if item.is_title():
                    eproject.data['note'] += '\n' + item['content']
                    edo.todoist2everdo.setdefault(item['id'],
                                                  eproject.data['id'])
                    continue
                add_item(edo, api, item, parent=eproject)
                added_items += 1

        for item in t.get_child_items():
            add_item(edo, api, item, parent=None)
            added_standalone_items += 1

    print("Added %d active projects, with %d items" % (added_projects,
                                                       added_items))
    print("Added %d standalone items" % added_standalone_items)


def get_inactive_labels(item):
    ret = set()
    for match in re.findall('__[a-zA-ZæøåÆØÅ]+', item['content']):
        lname = _escape_inactive_label(match)
        try:
            ret.add(item.api.get_label_id(lname))
        except Exception:
            # ignore missing labels
            # print("Not found label: {}".format(e))
            continue
        item['content'] = item['content'].replace(match, '').strip()
    return ret


def _escape_inactive_label(labelname):
    if labelname.startswith('__'):
        return labelname[2:]
    return labelname


def add_item(edo, api, item, list_type=None, parent=None,
             everdo_cls=everdo.Everdo_Action):
    """Add an action/item/note (not project)"""
    completed_on = due_date = None

    if not list_type:
        list_type = 'a'
        if item.is_waiting():
            list_type = 'w'

    if item['is_archived'] or item['date_completed']:
        if not list_type:
            list_type = 'r'
        completed_on = int(time.time())
        if 'date_completed' in item.data:
            completed_on = everdo.duedateutc2stamp(item['date_completed'])
    created_on = int(time.time())
    if item['date_added']:
        created_on = everdo.duedateutc2stamp(item['date_added'])
    if item['due_date_utc']:
        date = utils.parse_utc_to_datetime(item['due_date_utc'])
        due_date = everdo.datetime2stamp(date)
    if item['date_string'] and not item['due_date_utc']:
        print("WARN: due date mismatch?")
        print(" due_date_utc: %s" % item['due_date_utc'])
        print(" date_string: %s" % item['date_string'])
        print("Okay to only care about 'due_date_utc'?")
        print()

    # TODO: if date_string startswith (every or after): use schedule!

    tags = [edo.get_eid(l) for l in item['labels']]
    tags.extend(edo.get_eid(l) for l in get_inactive_labels(item))
    ret = everdo_cls(parent,
                     list_type=list_type,
                     title=item['content'],
                     completed_on=completed_on,
                     created_on=created_on,
                     due_date=due_date,
                     tags=tags)
    edo.add_item(ret, item)
    return ret


def add_someday(edo, api):
    added_projects = 0
    added_items = 0
    added_standalone_items = 0
    for t in api.get_somedaymaybe():
        for p in t.get_child_projects():
            if p['is_deleted']:
                continue
            completed_on = None
            if p['is_archived']:
                completed_on = int(time.time())
            eproject = everdo.Everdo_Project(
                    'm', p['name'], is_focused=p['is_favorite'],
                    completed_on=completed_on)
            edo.add_item(eproject, p)
            added_projects += 1

            # TODO: if the project has a due date, move it to scheduled
            # instead? Not sure if that is

            for item in p.get_child_items():
                if item['is_deleted']:
                    continue
                if item['due_date_utc']:
                    # Move project to scheduled if any date is set
                    eproject.data['list'] = 's'
                    start_date = everdo.duedateutc2stamp(item['due_date_utc'])
                    if (not eproject.data['start_date'] or
                            start_date < eproject.data['start_date']):
                        eproject.data['start_date'] = start_date
                if item.is_title():
                    eproject.data['note'] += '\n' + item['content']
                    edo.todoist2everdo.setdefault(item['id'],
                                                  eproject.data['id'])
                    continue
                add_item(edo, api, item, parent=eproject)
                added_items += 1

        for item in t.get_child_items():
            add_item(edo, api, item, parent=None, list_type='m')
            added_standalone_items += 1

    print("Added %d someday projects, with %d items" % (added_projects,
                                                        added_items))
    print("Added %d standalone someday items" % added_standalone_items)


def add_other_project(edo, api, pname):
    """Simply copy the project. Manual tweaks needed in Everdo afterwards."""
    p = api.get_project_by_name(pname)
    if p.get_child_projects():
        print("WARN: {} has child projects. What to do?".format(pname))
    if p['is_deleted']:
        print("WARN: {} is deleted. What to do?".format(pname))
        return

    completed_on = None
    if p['is_archived']:
        completed_on = int(time.time())
    eproject = everdo.Everdo_Project('a', p['name'],
                                     is_focused=p['is_favorite'],
                                     completed_on=completed_on)
    edo.add_item(eproject, p)

    for item in p.get_child_items():
        if item['is_deleted']:
            continue
        if item.is_title():
            eproject.data['note'] += '\n' + item['content']
            edo.todoist2everdo.setdefault(item['id'],
                                          eproject.data['id'])
            continue
        add_item(edo, api, item, parent=eproject)


def add_notebook(edo, api, pname):
    """Simply copy the project. Manual tweaks needed in Everdo afterwards."""
    p = api.get_project_by_name(pname)
    if p.get_child_projects():
        print("WARN: {} has child projects. What to do?".format(pname))
    if p['is_deleted']:
        print("WARN: {} is deleted. What to do?".format(pname))
        return

    completed_on = None
    if p['is_archived']:
        completed_on = int(time.time())
    notebook = everdo.Everdo_Notebook('a', p['name'],
                                      is_focused=p['is_favorite'],
                                      completed_on=completed_on)
    edo.add_item(notebook, p)

    for item in p.get_child_items():
        if item['is_deleted']:
            continue
        add_item(edo, api, item, parent=notebook,
                 everdo_cls=everdo.Everdo_Note)


def add_todoist_notes(edo, api):
    i = 0
    for note in api.notes.all():
        if note['is_deleted']:
            continue
        if note['is_archived']:
            continue
        if not note['content'].strip():
            continue
        try:
            eitem = edo.get_eitem(note['item_id'])
        except KeyError:
            item = api.items.get_by_id(note['item_id'])
            print("Can't find item id {} ({}) for note: {}"
                  .format(note['item_id'],
                          item['content'][:100].replace('\n', ' '),
                          note['content'][:100].replace('\n', ' ')))
            continue
        eitem.data['note'] += '\n' + note['content']
        i += 1
        # Add file attachments as direct links. Should I download them instead?
        if note['file_attachment']:
            for k in ('file_url', 'url'):
                url = note['file_attachment'].get(k)
                if url:
                    eitem.data['note'] += '\n' + url
    print("Added %d notes" % i)


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
    # TODO: add back when done testing:
    # api.fullsync()
    print("Full sync done")

    edo = everdo.Everdo_File()
    add_tags(edo, api)
    add_inbox(edo, api)
    add_active_projects(edo, api)
    add_someday(edo, api)
    for p in ("JobbRutiner", "PrivatRutiner", "Husarbeid", "Påminningar"):
        add_other_project(edo, api, p)
    add_notebook(edo, api, "Lesestund")
    add_todoist_notes(edo, api)

    edo.export(args.out)
    print("Exported %d items and %d tags" % (len(edo.items), len(edo.tags)))
    args.out.close()


if __name__ == '__main__':
    main()
