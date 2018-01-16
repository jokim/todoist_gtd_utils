#!/bin/env python
# -*- encoding: utf-8 -*-

""" Utility functionality for using Todoist.

Automating and batching changes in Todoist which isn't supported in the
official GUI.

TODO:
- Fix better config
- todoist's own code is not optimal for my use, e.g. at script startup and some
  bugs. Create my own, lightweight client, using the REST API directly?

"""

from datetime import datetime

import todoist
from todoist.api import SyncError
# TODO: move to utils, or somewhere else?
from termcolor import colored

from . import config
from . import utils
from . import userinput


class TodoistGTD(todoist.api.TodoistAPI):

    def __init__(self, token=None, configfiles=None):
        self.config = config.Config()
        if configfiles:
            self.config.read(configfiles)
        if not token:
            token = self.config.get('todoist', 'api-token')
        super(TodoistGTD, self).__init__(token=token)

        # Check if authenticated:
        if token:
            params = {'token': self.token,
                      'sync_token': '*',
                      'resource_types': '["labels"]',
                      }
            self._get('sync', params=params)

    def _get(self, call, url=None, **kwargs):
        """Override to raise HTTP errors"""
        if not url:
            url = self.get_api_url()

        response = self.session.get(url + call, **kwargs)
        response.raise_for_status()

        try:
            return response.json()
        except ValueError:
            return response.text

    def _post(self, call, url=None, **kwargs):
        """Override to raise HTTP errors"""
        if not url:
            url = self.get_api_url()

        response = self.session.post(url + call, **kwargs)
        response.raise_for_status()

        try:
            return response.json()
        except ValueError:
            return response.text

    def is_authenticated(self):
        """Return is user is authenticated.

        TBD: Double check with server if really authenticated?

        """
        return bool(self.token)

    def search(self, query):
        """Easier search API"""
        r = self.query((query,))
        if r:
            for i in r[0]['data']:
                yield HumanItem(i, self)

    def get_label_name(self, id):
        """Shortcut for getting a label's name"""
        if isinstance(id, (list, tuple, set)):
            return map(self.get_label_name, id)
        id = int(id)
        return self.labels.all(lambda x: x['id'] == id)[0]['name']

    def get_label_id(self, name):
        """Shortcut for getting a label's id"""
        if isinstance(name, (list, tuple, set)):
            return map(self.get_label_id, name)
        name = name.lower()
        for l in self.labels.all(lambda x: x['name'].lower() == name):
            # Label names must be unique, so will get max one result
            return l['id']
        raise Exception('No label with name: {}'.format(name))

    def get_label_humanname(self, id):
        """Retrieve a labels name with @ in front"""
        if isinstance(id, (list, tuple, set)):
            return map(self.get_label_humanname, id)
        return '@' + self.get_label_name(id)

    def get_project_name(self, id):
        """Shortcut for getting a project's name"""
        if isinstance(id, (list, tuple, set)):
            return map(self.get_project_name, id)
        if isinstance(id, todoist.models.Project):
            return id['name']
        return self.projects.all(lambda x: x['id'] == id)[0]['name'].strip()

    def get_projects_by_name(self, name, raise_on_duplicate=True):
        """Find a project by its given name.

        :type name: str
        :param name:
            The name of the project. Must match exact, but whitespace around is
            ignored.

        :type raise_on_duplicate: bool
        :param raise_on_duplicate:
            Set to True if you assert that only one project exist with given
            name. If True, an exception is raised if more than one project
            exist with given name, and a Project is returned instead of a list.

        :rtype: list or todoist.models.Project
        :return:
            Returns one *Project* object if `raise_on_duplicate` is True,
            otherwise a list of Project objects.

        """
        name = name.strip()
        ret = []
        for p in self.projects.all():
            if p['name'].strip() == name:
                ret.append(p)
        if raise_on_duplicate:
            if len(ret) > 1:
                raise Exception("Several projects with name: {}".format(name))
            if len(ret) == 0:
                raise Exception("No project with name: {}".format(name))
            return ret[0]
        return ret

    def get_child_projects(self, parent):
        """Get a list of all child projects of a given project

        Would like to use p['parent_id'], but it's not set for all children,
        unfortunately. Instead, children are all projects with a higher indent
        and item_order.

        :type parent: todoist.models.Project
        :param parent: The target project to fetch children for

        :rtype: list
        :return: A list of Project objects

        """
        ret = []
        order = parent['item_order']
        projs = self.projects.all(lambda x: x['item_order'] > order)
        projs.sort(key=lambda x: x['item_order'])
        for p in projs:
            if p['indent'] <= parent['indent']:
                break
            ret.append(p)
        return ret

    def force_commit(self):
        """Make sure a commit with Todoist is commited.

        Sometimes, the sync fails due to "Invalid temporary id
        (INVALID_TEMPID)". Haven't dug out the cause, but a retry most often
        fix the issue:

        """
        try:
            self.commit(raise_on_error=True)
        except SyncError:
            self.commit(raise_on_error=True)
        return True

    def fullsync(self):
        """Force a fullsync, since `sync()` fails sometimes.

        Completed items aren't always updated locally.

        You could instead just remove local cache files.

        """
        self.reset_state()
        self.sync()

class GTDItem(todoist.models.Item):
    """Add GTD functionality, and more, to tasks."""

    def is_due(self):
        """Return True if task is due today or overdue"""
        # TODO: Verify that it's ONLY 'due_date_utc' that is used. Could
        # 'date_string' be checked as well?
        due = self.data['due_date_utc']
        if not due:
            return False
        due_date = utils.parse_utc_to_datetime(self.data['due_date_utc'])
        return due_date <= datetime.today()


class HumanItem(GTDItem):
    """Simpler representation of a todoist item (task)."""

    def get_frontend_pri(self):
        """Return priority in frontend's perspective.

        The API considers 4 as the highest priority, while the frontend
        considers that as 1.

        """
        p = self['priority']
        if p == 4:
            return 1
        if p == 3:
            return 2
        if p == 2:
            return 3
        return 4

    def get_presentation(self):
        """Get details about the item, in a presentable manner.

        Uses a few lines, and colors!

        """
        max = userinput.get_terminal_size()[1]
        ret = []
        ret.append(utils.trim_too_long(self.data.get('content'), max))
        sub = []
        if self.data.get('date_string'):
            sub.append(colored('[{}]'.format(self['date_string'] or ''),
                               'magenta', attrs=['bold']))
        pri = self.get_frontend_pri()
        if pri < 4:
            sub.append(colored('!!{}'.format(pri), 'red', attrs=['bold']))
        if 'labels' in self.data:
            labels = self.api.get_label_humanname(self['labels'])
            if labels:
                sub.append(colored(' '.join(labels), 'green'))
        if 'project_id' in self.data:
            sub.append(colored(utils.trim_too_long(
                '#' + self.api.get_project_name(self['project_id']),
                max - len(' '.join(sub))), 'blue'))
        ret.append(' '.join(sub))
        return '\n'.join(ret)

    def get_short_preview(self):
        """Get one line with details of the item"""
        max = userinput.get_terminal_size()[1]
        ret = []
        if self.data.get('date_string'):
            ret.append(colored('[{}]'.format(self['date_string'] or ''),
                               'magenta', attrs=['bold']))
        pri = self.get_frontend_pri()
        if pri < 4:
            ret.append(colored('!!{}'.format(pri), 'red', attrs=['bold']))
        ret.append('|')
        if 'labels' in self.data:
            labels = self.api.get_label_humanname(self['labels'])
            if labels:
                ret.append(colored(' '.join(labels), 'green'))
        if 'project_id' in self.data:
            ret.append(colored(utils.trim_too_long(
                '#' + self.api.get_project_name(self['project_id']), 30),
                'blue'))
        ret = ' '.join(ret)
        return (utils.trim_too_long(self.data.get('content'), max-len(ret)-1) +
                ' ' + ret)

    def __unicode__(self):
        return self.get_short_preview()

    def __str__(self):
        return self.get_short_preview().encode('utf-8')


todoist.models.Item = HumanItem
