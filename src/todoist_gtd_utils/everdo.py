#!/bin/env python
# -*- encoding: utf-8 -*-

""" Utils for Everdo

See https://everdo.net for the Everdo application.

See https://forum.everdo.net/t/import-data-format/106/3 for its import data
format. Example on file::

    "items": [
        {
            "id": "BD651DDD391145F9B78C2980B2D547F7",
            "type": "n",
            "list": "a",
            "note": "Everdo is not a note-taking app.\nUse notes…",
            "completed_on": null,
            "parent_id": "297CC45E929D4B30A71EB783F53B9119",
            "title": "Don't try to put the whole world's knowledge into notes",
            "created_on": 1514329200,
            "is_focused": 0,
            "energy": null,
            "time": null,
            "due_date": null,
            "start_date": null,
            "schedule": null,
            "recurrent_task_id": "",
            "contact_id": "",
            "tags": [],
            "position_child": 5,
            "position_parent": null,
            "position_focus": null,
            "position_global": null,
            "repeated_on": null
        },
        ...
    ],
    "tags": [
        {
            "id": "CE766CF141B44E4CBA645F22F242EEF9",
            "title": "Work",
            "title_ts": null,
            "color": 16739166,
            "color_ts": 1546082578,
            "type": "a",
            "type_ts": null,
            "created_on": null,
            "changed_ts": 1546082578,
            "removed_ts": null
        }
        ...
    ],

TODO:

- What is the *_ts variables?

"""

from __future__ import unicode_literals

import calendar
import datetime
import json
import time
import uuid

from . import utils


def gen_uuid():
    """ Create an UUID4 as Everdo wants it.

    «Those are GUIDs. You can create your own random UUID-4. Make sure it’s
    an uppercase string without dashes. When referring to another item,
    make sure it really exists.»

    """
    return uuid.uuid4().hex.upper()


def encode(data):
    """Encode unicode to utf8 recursively

    (Yes, switching to py3 would be easier…)

    """
    if isinstance(data, (Everdo_Tag, Everdo_Item)):
        return encode(data.data)
    if isinstance(data, dict):
        return dict((k, encode(v)) for k, v in data.iteritems())
    if isinstance(data, (list, tuple)):
        return tuple(encode(i) for i in data)
    if isinstance(data, unicode):
        return data.encode('utf-8')
    return data


def duedateutc2stamp(dat):
    """Parse date from Todoists `due_date_utc` to UNIX timestamp"""
    return datetime2stamp(utils.parse_utc_to_datetime(dat))


def datetime2stamp(dat):
    """Note: only the date, not time, included!"""
    if isinstance(dat, datetime.datetime):
        dat = dat.date()
    return calendar.timegm(dat.timetuple())


class Everdo_File(object):
    def __init__(self):
        self.items = []
        # TODO: what more?
        self.tags = []
        # Map from Todoist to Everdo IDs
        self.todoist2everdo = {}
        # All items, by their ID
        self.eitems = {}

    def export(self, fp):
        output = {'items': encode(self.items),
                  'tags': encode(self.tags),
                  }
        json.dump(output, fp, ensure_ascii=False, indent=4)

    def add_tag(self, etag, tlabel):
        self.tags.append(etag)
        self.todoist2everdo[tlabel['id']] = etag.data['id']

    def add_item(self, eitem, titem):
        self.items.append(eitem)
        self.todoist2everdo[titem['id']] = eitem.data['id']
        self.eitems[eitem.data['id']] = eitem

    def get_eid(self, t_id):
        return self.todoist2everdo[t_id]

    def get_eitem(self, t_id):
        eid = self.todoist2everdo[t_id]
        return self.eitems[eid]


class Everdo_Schedule(dict):
    """Handle the Schedule model for Everdo.

    Based on best guesses… Example::

        "schedule": {
            "type": "Daily",
            "period": 1,
            "daysOfWeek": null,
            "daysOfMonth": null,
            "daysOfYear": null,
            "limit": null,
            "endDate": null
        },

    """
    def __init__(self, type=None, period=None, daysOfWeek=None,
                 daysOfMonth=None, daysOfYear=None, limit=None, endDate=None):
        vars = locals()
        del vars['self']
        super(Everdo_Schedule, self).__init__(**vars)


class Everdo_Tag(object):
    """A tag in the Everdo file format"""

    tag_types = (
        "c",  # contact
        "a",  # area
        "l",  # label
        # TODO; others?
    )

    def __init__(self,
                 tag_type,
                 title,
                 created_on=None,
                 tag_type_ts=None,
                 title_ts=None,
                 color=None,
                 color_ts=None,
                 changed_ts=None,
                 removed_ts=None):
        """ Create tag.

        :param tag_type:
            What kind of tag this is, e.g. contact, label or area. See
            `self.tag_types` for valid types.

        :param title: Tags title.

        :type created_on: str
        :param created_on:
            Creation date. Format: UNIX timestamp - seconds since UNIX epoch.
            The timestamp’s time must be set to 00:00:00.

        TODO: What's the *_ts parameters?

        """
        assert tag_type in self.tag_types, "Invalid tag type"

        if not created_on:
            created_on = int(time.time())

        self.data = {
                'id': gen_uuid(),
                'title': title,
                'title_ts': title_ts,
                'color': color,
                'color_ts': color_ts,
                'type': tag_type,
                'type_ts': tag_type_ts,
                'created_on': created_on,
                'changed_ts': changed_ts,
                'removed_ts': removed_ts,
                }
        # Add positions?


class Everdo_Item(object):
    """An item in the Everdo file format"""

    list_types = (
        "i",  # inbox (actions only)
        "a",  # active/next (based on item type)
        "m",  # someday
        "s",  # scheduled (must also specify start_date or schedule field)
        "w",  # waiting
        "d",  # deleted
        "r",  # archived (must also specify completed_on)
    )

    def __init__(self,
                 list_type,
                 title,
                 created_on=None,
                 is_focused=False,
                 start_date=None,
                 schedule=None,
                 completed_on=None,
                 energy=None,
                 time_estimate=None,
                 due_date=None,
                 recurrent_task_id=None,
                 contact_id=None,
                 note="",
                 tags=(),
                 repeated_on=None,
                 positions=None):
        """ Create item.

        :param list_type:
            In what list the item is places, e.g. `i` for inbox or `w` for
            waiting. See `self.list_types` for valid types.

        :param title: Items title.

        :type created_on: str
        :param created_on:
            Creation date. Format: UNIX timestamp - seconds since UNIX epoch.
            The timestamp’s time must be set to 00:00:00.

        :param is_focused:
            Values: 0 or 1. Warning: True and False will not work.

        :param completed_on:
            UNIX timestamps in seconds. If not null, then the item is
            considered “done”.

        :param energy:
            Energy estimate. Values: null, 1, 2, 3

        :param time_estimate:
            Time estimate. Value: number of minutes

        :param due_date:
            Optional due date. The timestamp’s time must be set to 00:00:00.

        :param start_date:
            For one-time scheduled items only. The timestamp’s time must be set
            to 00:00:00.

        :param schedule:
            Not supported, for now.

            For repeating items only. More complex, can’t describe this one off
            the top of my head :wink: Try exporting something and see for
            yourself.

        :param recurrent_task_id:
            Not supported, for now.

            The “template” action that was used to create an instance of this
            specific repeating action.

        :param contact_id:
            Optional contact tag to wait for. The value is tag id.

        :param tags:
            an array of tag ids.

        :param repeated_on:
            Indicates when was the last time a repeating item was created.

        :param positions:
            Not supported, for now.

            Item’s position in a specific list:

            - child: position in a list of all sub-items (project actions /
              notes)

            - parent: position in a list of all parent items
              (projects/notebooks)

            - focus: position in a global focus list

            - global: position in a the list of all items

        """
        assert list_type in self.list_types, "Bad list type: %s" % list_type

        if not created_on:
            created_on = int(time.time())

        self.data = {
                'id': gen_uuid(),
                'list': list_type,
                'title': title,
                'created_on': created_on,
                'is_focused': int(bool(is_focused)),
                'start_date': start_date,
                'schedule': schedule,
                'completed_on': completed_on,
                'energy': energy,
                'time_estimate': time_estimate,
                'due_date': due_date,
                'recurrent_task_id': recurrent_task_id,
                'contact_id': contact_id,
                'tags': tags,
                'repeated_on': repeated_on,
                'note': note,
                }
        # Add positions?


class Everdo_Action(Everdo_Item):
    def __init__(self, parent, *args, **kwargs):
        """ Create action

        :type parent: Everdo_Project
        :param parent:
            The parent project for this action. Can be None, for standalone.

        """
        super(Everdo_Action, self).__init__(*args, **kwargs)
        if 'type' not in self.data:
            self.data['type'] = 'a'
        if parent:
            self.data['parent_id'] = parent.data['id']


class Everdo_Project(Everdo_Item):
    def __init__(self, *args, **kwargs):
        super(Everdo_Project, self).__init__(*args, **kwargs)
        if 'type' not in self.data:
            self.data['type'] = 'p'


class Everdo_Note(Everdo_Item):
    def __init__(self, parent, *args, **kwargs):
        """ Create note

        :type parent: Everdo_Note
        :param parent:
            The parent project or notebook for this action. Can be None, for
            standalone items.

        """
        super(Everdo_Note, self).__init__(*args, **kwargs)
        if 'type' not in self.data:
            self.data['type'] = 'n'
        if parent:
            self.data['parent_id'] = parent.data['id']


class Everdo_Notebook(Everdo_Item):
    def __init__(self, *args, **kwargs):
        super(Everdo_Notebook, self).__init__(*args, **kwargs)
        if 'type' not in self.data:
            self.data['type'] = 'l'
