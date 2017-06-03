#!/bin/env python
# -*- encoding: utf-8 -*-

""" Utility functionality for using Todoist.

Automating and batching changes in Todoist which isn't supported in the
official GUI.

TODO:
- Fix better config

"""

import todoist

from . import config
from . import utils


class TodoistGTD(todoist.api.TodoistAPI):

    def __init__(self, token=None, configfiles=None):
        self.config = config.Config()
        if configfiles:
            self.config.read(configfiles)
        if not token:
            token = self.config.get('todoist', 'api-token')
        super(TodoistGTD, self).__init__(token)

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

        :type parent: todoist.models.Project
        :param parent: The target project to fetch children for

        :rtype: list
        :return: A list of Project objects

        """
        ret = []
        projs = self.projects.all()
        projs.sort(key=lambda x: x['item_order'])
        found = False
        for p in projs:
            # Would like to use p['parent_id'], but it's not set for all
            # children, unfortunately. Instead, children are all projects with
            # a higher indent and item_order.
            if p['id'] == parent['id']:
                found = True
            elif found:
                if p['indent'] > parent['indent']:
                    ret.append(p)
                else:
                    found = False
        return ret


class HumanItem(todoist.models.Item):
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

    def get_short_preview(self):
        ret = utils.trim_too_long(self.data.get('content'), 100)
        if self.data.get('date_string'):
            ret += ' [{}]'.format(self['date_string'] or '')
        pri = self.get_frontend_pri()
        if pri < 4:
            ret += ' !!{}'.format(pri)
        ret += " ("
        if 'labels' in self.data:
            labels = ' '.join(self.api.get_label_humanname(self['labels']) or
                              ())
            ret += labels
        if 'project_id' in self.data:
            ret += utils.trim_too_long(
                    ' #' + self.api.get_project_name(self['project_id']), 30)
        ret += ")"
        return ret

    def __unicode__(self):
        return self.get_short_preview()

    def __str__(self):
        return self.get_short_preview()

todoist.models.Item = HumanItem
