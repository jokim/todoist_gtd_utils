#!/bin/env python
# -*- encoding: utf-8 -*-

"""Functionality for simple menus for interaction with user."""

from __future__ import unicode_literals

from todoist_gtd_utils import userinput


def menu_project(api, project, extra=None):
    """Present a menu to modify a project.

    :type project: todoist.model.Project
    :param project: Given project the user could do something with.

    :type extra: TODO
    :param extra: If you want extra actions. Could override existing commands.

    :raises EOFError:
        When user presses CTRL+D. Should be treated as "go back" or cancel. The
        input of 'q' means "done" and *might* be treated differently.

    """
    # Define callbacks for actions
    # (probably a much better way doing this generically…)
    def archive_project():
        project.archive()
        print("Project archived")

    def delete_project():
        project.delete()
        print("Project deleted")

    def activate_project():
        targetprojects = api.config.get_commalist('gtd', 'target-projects')
        project_id = None
        if len(targetprojects) == 1:
            project_id = api.get_projects_by_name(targetprojects[0])
        elif len(targetprojects) > 1:
            project_id = userinput.ask_choice('Where to?',
                                              choices=targetprojects,
                                              default=0, category="project")
        else:
            print("No target projects defined. Where to move?")
            project_id = userinput.ask_project(api)
        project.activate(project_id)
        print("Project activated")

    def hibernate_project():
        project.hibernate()
        print("Project moved to Someday/Maybe")

    def create_item():
        userinput.dialog_new_item(api, project=project)
        print("Next action created")
        # TODO: menu for item

    def view_project():
        project.print_presentation()

    def go_parent():
        try:
            parent = project.get_parent_project()
        except IndexError:
            print("No parent for given project, cancel")
            return

        try:
            menu_project(api, parent)
        except EOFError:
            print("Going back to project {}".format(project))

    userinput.ask_menu(
        {'d': ('Set project to done (archive)', archive_project),
         'a': ('Activate project', activate_project),
         'v': ('View project', view_project),
         'h': ('Hibernate project (Someday/Maybe)', hibernate_project),
         'Gp': ('Go to parent project', go_parent),
         'Ga': ('Go to an action', go_parent),
         'c': ('Create next action', create_item),
         'D': ('Delete project', delete_project),
         },
        prompt="For project {}, what to do?".format(project))
    api.force_commit()


def menu_item(api, item, extra=None):
    """Present a menu to modify an item.

    :type item: todoist.model.Item
    :param item: Given item the user could do something with.

    :type extra: TODO
    :param extra: If you want extra actions. Could override existing commands.

    :raises EOFError:
        When user presses CTRL+D. Should be treated as "go back" or cancel.

    """
    # Define callbacks for actions
    def archive_item():
        item.archive()
        api.force_commit()
        print("Action archived")

    def delete_item():
        item.delete()
        api.force_commit()
        print("Action deleted. Most commands now doesn't work.")

    def set_project():
        # TODO: move to a helper method in userinput?
        projects = dict((p['id'], unicode(p['name'])) for p in
                        api.projects.all())
        project_id = userinput.ask_choice('Project', choices=projects,
                                          default=item['project_id'],
                                          category="project")
        item.move_to_project(project_id)
        api.force_commit()
        print("Project set")

    def add_note():
        # TODO: Ask for input
        print("TODO")
        api.force_commit()
        pass

    def edit_note():
        print("TODO")
        api.force_commit()
        # TODO: Make it's own menu for this?
        # 1. list attachments
        # 2. choose an attachment
        # 3. start editor to edit it
        # 4. if saved, update in todoist
        pass

    def view_item():
        print(item.get_presentation())
        item.print_note_preview()

    def move_item():
        # TODO: ask for to what project
        api.force_commit()
        print("TODO")

    def set_labels():
        l = userinput.ask_labels(api, api.get_label_name(item['labels']))
        item.update(labels=l)
        api.force_commit()
        print("Labels updated")

    def set_date():
        d = userinput.ask_date(api, item['date_string'])
        item.update(date_string=d)
        api.force_commit()
        print("Date updated")

    def set_priority():
        p = userinput.ask_priority(api, item['priority'])
        item.update(priority=p)
        api.force_commit()
        print("Priority updated")

    def set_description():
        description = userinput.ask_description(api, item['content'])
        item.update(content=description)
        api.force_commit()
        print("Description updated")

    print("In item {}".format(item))
    userinput.ask_menu(
        {'D': ('Set action to done (archive)', archive_item),
         'd': ('Set date', set_date),
         'e': ('Edit description', set_description),
         'v': ('View action', view_item),
         'l': ('Set labels', set_labels),
         'm': ('Move item to Someday/Maybe', move_item),
         'n': ('Create new note', add_note),
         'p': ('Set project', set_project),
         't': ('Set priority', set_priority),
         'Gn': ('Go to a note to edit (EDITOR?)', edit_note),
         'Gp': ("Go to item's project", menu_project),
         'Del': ('Delete item', delete_item),
         },
        prompt="What to do?")
    api.force_commit()
