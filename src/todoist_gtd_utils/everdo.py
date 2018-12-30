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


"""

from __future__ import unicode_literals

import json
import uuid


def gen_uuid(self):
    """ Create an UUID4 as Everdo wants it.

    «Those are GUIDs. You can create your own random UUID-4. Make sure it’s
    an uppercase string without dashes. When referring to another item,
    make sure it really exists.»

    """
    return uuid.uuid4().hex.upper()


class Everdo_File(object):
    def __init__(self):
        self.items = []
        # TODO: what more?
        self.tags = []

    def export(self, file):
        fp = open(file, 'w')
        output = {'items': self.items,
                  'tags': self.tags,
                  }
        json.dump(output, fp, ensure_ascii=False, indent=4)


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
                 created_on,
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
                 created_on,
                 is_focused=False,
                 start_date=None,
                 schedule=None,
                 completed_on=None,
                 energy=None,
                 time_estimate=None,
                 due_date=None,
                 recurrent_task_id=None,
                 contact_id=None,
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
        assert list_type in self.list_types, "Invalid list type"

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
                }
        # Add positions?


class Everdo_Action(Everdo_Item):
    def __init__(self, parent, *args, **kwargs):
        """ Create action

        :type parent: Everdo_Project
        :param parent:
            The parent project for this action. Can be None, for standalone.

        """
        super(Everdo_Action, self).__init__(self, *args, **kwargs)
        if 'type' not in self.data:
            self.data['type'] = 'a'
        if parent:
            self.data['parent_id'] = parent.data['id']


class Everdo_Project(Everdo_Item):
    def __init__(self, *args, **kwargs):
        super(Everdo_Action, self).__init__(self, *args, **kwargs)
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
        super(Everdo_Action, self).__init__(self, *args, **kwargs)
        if 'type' not in self.data:
            self.data['type'] = 'n'
        if parent:
            self.data['parent_id'] = parent.data['id']


class Everdo_Notebook(Everdo_Item):
    def __init__(self, *args, **kwargs):
        super(Everdo_Action, self).__init__(self, *args, **kwargs)
        if 'type' not in self.data:
            self.data['type'] = 'l'
