#!/bin/env python
# -*- encoding: utf-8 -*-

import requests
import todoist



class TodoistGTD(todoist.api.TodoistAPI):

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

    def search(self, query):
        """Easier search API"""
        r = self.query((query,))
        if r:
            for i in r[0]['data']:
                yield HumanItem(i, self)

    def get_label_name(self, id):
        """Shortcut for getting a label's name"""
        return '@' + self.labels.get_by_id(id)['name']

    def get_project_name(self, id):
        """Shortcut for getting a project's name"""
        return '#' + self.projects.get_by_id(id)['name']

    def get_projects_by_name(self, name, raise_on_duplicate=True):
        """Find a project by its given name.

        :type name: str
        :param name:
            The name of the project. Must match exact, but whitespace around is
            ignored.

        :type raise_on_duplicate: bool
        :param raise_on_duplicate:
            Set to True if you assert that only one project exist with given
            name. If True, an exception is raised if more than one project exist
            with given name, and a Project is returned instead of a list.

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
            if len(ret) != 1:
                raise Exception("Several projects with name: {}".format(name))
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

    def __unicode__(self):
        ret = self['content']
        if self['date_string']:
            ret += ' [{}]'.format(self['date_string'])
        if self['labels']:
            ret += ' ' + ' '.join(map(self.api.get_label_name, self['labels'] or
                ()))
        #ret += ' ' + self.api.get_project_name(self['project_id'])
        return ret

todoist.models.Item = HumanItem
