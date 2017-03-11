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

    def get_child_projects(self, parent):
        """Get a list of all child projects of a given project

        :type parent: todoist.model.Project
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
