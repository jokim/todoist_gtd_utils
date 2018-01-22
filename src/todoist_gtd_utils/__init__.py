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

    def get_label_id(self, name, raise_on_missing=True):
        """Shortcut for getting a label's id"""
        if isinstance(name, (list, tuple, set)):
            return filter(None,
                          (self.get_label_id(n,
                                             raise_on_missing=raise_on_missing)
                           for n in name))
        name = name.lower()
        for l in self.labels.all(lambda x: x['name'].lower() == name):
            # Label names must be unique, so will get max one result
            return l['id']
        if raise_on_missing:
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


class HelperProject(todoist.models.Project):
    """Helper methods for project"""

    def get_child_projects(self):
        """Get a list of all child projects of self

        Children are all projects with a item_order, and a larger indent. The
        range breaks when a project has an indent that is equal or lower than
        `self`. The element p['parent_id'] is not set for all children,
        unfortunately, so we ignore that one.

        :rtype: list
        :return: A list of Project objects

        """
        ret = []
        order = self['item_order']
        indent = self['indent']
        projs = self.api.projects.all(lambda x: x['item_order'] > order)
        projs.sort(key=lambda x: x['item_order'])
        for p in projs:
            if p['indent'] <= indent:
                break
            ret.append(p)
        return ret

    def _move_project(self, new_parent):
        """Move self to new given parent project.

        The order in sub project list is, for now, set to the middle.

        """
        # Find the right order
        children = new_parent.get_child_projects()
        # Take the median value, to put it in the middle
        new_order = children[len(children)/2]['item_order']
        return self.update(indent=new_parent['indent'] + 1,
                           item_order=new_order)

    def activate_project(self, parent_project=None):
        """Move project from Someday/Maybe to active projects.

        :type parent_proj: str
        :param parent_proj:
            What parent project to move this to. Should be a GTD specific
            project in Todoist, either "GTD" or something more granular, like
            "Personal" and "Work.

        """
        if not parent_project:
            parent_project = self.config.get_commalist('gtd',
                                                       'target-projects')[0]
        self._move_project(parent_project)
        # TODO: more to do?

    def postpone_project(self, someday_project=None):
        """Move project to Someday/Maybe."""
        if not someday_project:
            # TODO: Get from config?
            someday_project = self.api.get_projects_by_name('Someday Maybe')
        self._move_project(someday_project)
        # TODO: more to do?

    def get_child_items(self, include_child_projects=False):
        """Return all items in the project."""
        project_ids = [self['id']]
        if include_child_projects:
            project_ids.extend(p['id'] for p in self.get_child_projects())
        return self.api.items.all(lambda x: x['project_id'] in project_ids)

    def get_notes(self):
        return self.api.project_notes.all(
                                    lambda x: x['project_id'] == self['id'])

    def print_presentation(self):
        """Get details about the project, in a presentable manner.

        Uses a few lines, and colors!

        """
        print(self.get_short_preview())
        children = self.get_child_projects()
        if children:
            print("\nChild project:")
            for child in children:
                print(child)

        print('\nItems:')
        items = self.get_child_items()
        if not items:
            print("(found no items)")
        for item in items:
            print(item)

        notes = self.get_notes()
        if notes:
            print("\nProject notes:")
            for note in notes:
                print(note)

    def get_short_preview(self):
        """Get one line with details of the project.

        It tries to fit in a single terminal line, so the project name gets
        shortened in small terminal windows.

        """
        max = userinput.get_terminal_size()[1]
        pre = []
        pre.append(' ' * (self['indent'] - 1))
        if self['is_deleted']:
            pre.append("[DELETED]")
        if self['is_archived']:
            pre.append("[ARCHIVED]")

        post = []
        # TODO: Include summary of the project's items? E.g.
        # - the number of active items
        # - next due date in project

        if self['has_more_notes']:
            # TODO: get the number of notes
            post.append("(X notes)")

        restlen = len(' '.join(pre)) + len(' '.join(post))
        pre.append(colored(utils.trim_too_long(self['name'], max-restlen),
                           color='blue'))
        pre.extend(post)
        return ' '.join(pre)

    def __unicode__(self):
        return self.get_short_preview()

    def __str__(self):
        return self.__unicode__().encode('utf-8')


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

    def is_title(self):
        """Tell if task is a title, i.e. not a task that can be completed.

        Titles are recognised by starting with an asterisk, or ending with a
        colon. There are probably additional title formats, as well.

        """
        return (self['content'].startswith('* ') or
                self['content'].endswith(':'))

    def is_actionable(self):
        """Return True if this is a normal, completable task."""
        return not self.is_title()

    def get_project(self):
        """Return the item's project instance."""
        return self.api.projects.get_by_id(self['project_id'])


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


class HelperProjectNote(todoist.models.ProjectNote):

    def get_posted_time(self):
        """Get a proper datetime object for the time posted"""
        return utils.parse_utc_to_datetime(self['posted'])

    def __unicode__(self):
        max = userinput.get_terminal_size()[1]
        post = []
        if self['file_attachment']:
            post.append(colored(self['file_attachment'], attrs=['underline']))
        post.append(self.get_posted_time().strftime('%Y-%M-%d %H:%m'))
        poststr = ' | '.join(post)
        content = utils.trim_too_long(self['content'],
                                      max - 3 - len(poststr)).replace('\n', ' ')
        return (colored(content, attrs=['dark']) + ' | ' + poststr)

    def __str__(self):
        return self.__unicode__().encode('utf-8')


todoist.models.Item = HumanItem
todoist.models.Project = HelperProject
todoist.models.ProjectNote = HelperProjectNote
