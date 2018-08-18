#!/bin/env python
# -*- encoding: utf-8 -*-

""" Testing main functionality.

"""

import requests
import mock
from pytest import raises

import todoist_gtd_utils
from todoist_gtd_utils import exceptions


def get_blank_api():
    """Return Todoist api ready for testing"""
    mock_ses = mock.create_autospec(requests.Session(), spec_set=True)
    api = todoist_gtd_utils.TodoistGTD(session=mock_ses, cache=None)
    return api


example_data = {
    'labels': ['home', 'office', 'computer', 'phone'],
    'projects': [
        {'name': 'Project X', 'items': [
            {'content': 'First, do A', 'labels': ['home'],
             'date_string': 'today', 'indent': 1},
            {'content': 'Then, do B', 'labels': ['office'],
             'date_string': 'tomorrow', 'indent': 1},
        ], 'indent': 1},
        {'name': 'Project Y'},
        {'name': 'Project Z', 'items': [{'content': 'Talk with someone…'}]},
    ],
}


def get_filled_api(data=example_data):
    api = get_blank_api()
    for label in data.get('labels', ()):
        api.labels.add(label)
    for project in data.get('projects', ()):
        p = api.projects.add(project['name'], indent=project.get('indent', 1))
        for item in project.get('items', ()):
            if 'labels' in item:
                labels = api.get_label_id(item['labels'])
            else:
                labels = None
            api.items.add(item['content'], project_id=p['id'],
                          indent=item.get('indent', 1),
                          date_string=item.get('date_string', ''),
                          labels=labels)
    api.commit()
    return api


@mock.patch('todoist.api.requests')
def test_main(mock_req):
    # TODO: this is checking online
    todoist_gtd_utils.TodoistGTD()


def test_empty_api():
    api = get_blank_api()
    assert len(api.projects.all()) == 0
    assert len(api.items.all()) == 0
    assert len(api.labels.all()) == 0
    assert len(api.notes.all()) == 0
    api.projects.add('test')
    api.commit()
    assert len(api.projects.all()) == 1
    # And test reset:
    api = get_blank_api()
    assert len(api.projects.all()) == 0


def test_filled_api():
    api = get_filled_api(example_data)
    assert len(api.labels.all()) == len(example_data['labels'])
    assert len(api.projects.all()) == len(example_data['projects'])

    for p in example_data['projects']:
        todo_p = api.get_project_by_name(p['name'])
        assert len(p.get('items', ())) == len(todo_p.get_child_items())


def test_get_project_by_name():
    api = get_blank_api()
    p = api.projects.add('test3000')
    api.commit()
    assert api.get_project_by_name('test3000') == p
    matches = api.get_projects_by_name('test3000')
    assert len(matches) == 1
    assert matches[0] == p

    with raises(exceptions.NotFoundError):
        api.get_project_by_name('notest99999')
    assert api.get_projects_by_name('notst99999') == []


def test_get_project_by_name_duplicate():
    api = get_blank_api()
    p1 = api.projects.add('test3000')
    p2 = api.projects.add('test3000')
    api.commit()
    with raises(exceptions.DuplicateError):
        api.get_project_by_name('test3000')

    matches = api.get_projects_by_name('test3000')
    assert len(matches) == 2
    assert p1 in matches
    assert p2 in matches
