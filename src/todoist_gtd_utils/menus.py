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
        # TODO: check if project is already active
        targetprojects = api.config.get_commalist('gtd', 'target-projects')
        if len(targetprojects) == 1:
            parent = api.get_projects_by_name(targetprojects[0])
        elif len(targetprojects) > 1:
            choice = userinput.ask_choice('Where to?', choices=targetprojects,
                                          default=0, category="project")
            parent = api.get_projects_by_name(targetprojects[choice])
        else:
            print("No target projects defined. Where to move?")
            parent = userinput.ask_project(api)
        project.activate(parent)
        print("Project activated")

    def hibernate_project():
        hibernated = api.config.get_commalist('gtd', 'someday-projects')
        if len(hibernated) == 1:
            parent = api.get_projects_by_name(hibernated[0])
        elif len(hibernated) > 1:
            choice = userinput.ask_choice('Where to?', choices=hibernated,
                                          default=0, category="project")
            parent = api.get_projects_by_name(hibernated[choice])
        else:
            print("No someday projects defined. Where to move?")
            parent = userinput.ask_project(api)
        project.hibernate(parent)
        print("Project hibernated to {}".format(parent))

    def move_project():
        print("Choose new parent project:")
        new_parent = userinput.ask_project(api)
        project.move_project(new_parent)
        print('Project moved')

    def create_item():
        userinput.dialog_new_item(api, project=project)
        print("Next action created")
        # TODO: menu for item?

    def view_project():
        project.print_presentation()

    def set_description():
        description = userinput.ask_description(api, project['name'])
        project.update(name=description)
        api.force_commit()
        print("Description updated")

    def add_note():
        print("TODO, add project note missing")
        # TODO
        pass

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
        {'D': ('Set project to done (archive)', archive_project),
         'v': ('View project', view_project),
         'Del': ('Delete project', delete_project),
         'a': ('Activate project', activate_project),
         'h': ('Hibernate project (Someday/Maybe)', hibernate_project),
         'm': ('Move to another parent', move_project),
         'e': ('Edit description (project name)', set_description),
         'c': ('Create next action', create_item),
         'n': ('Create new project note', add_note),
         # Navigation
         'Gp': ('Go to parent project', go_parent),
         'Ga': ('Go to an action', go_parent),
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
        item.complete()
        api.force_commit()
        print("Action archived")

    def delete_item():
        item.delete()
        api.force_commit()
        print("Action deleted. Most commands now doesn't work.")

    def move_item():
        project = userinput.ask_project(api, default=item.get_project())
        item.move_to_project(project)
        api.force_commit()
        print("Project set")

    def add_note():
        # TODO: Ask for input
        # Should we be able to ask to fetch e.g. from an URL, or file, or just
        # start the editor?
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

    def activate_item():
        targetprojects = api.config.get_commalist('gtd', 'target-projects')
        if len(targetprojects) == 1:
            parent = api.get_projects_by_name(targetprojects[0])
        elif len(targetprojects) > 1:
            choice = userinput.ask_choice('Where to?', choices=targetprojects,
                                          default=0, category="project")
            parent = api.get_projects_by_name(targetprojects[choice])
        else:
            print("No target projects defined. Where to move?")
            parent = userinput.ask_project(api)
        item.activate(parent)
        print("Item activated")

    def hibernate_item():
        hibernated = api.config.get_commalist('gtd', 'someday-projects')
        if len(hibernated) == 1:
            parent = api.get_projects_by_name(hibernated[0])
        elif len(hibernated) > 1:
            choice = userinput.ask_choice('Where to?', choices=hibernated,
                                          default=0, category="project")
            parent = api.get_projects_by_name(hibernated[choice])
        else:
            print("No someday projects defined. Where to move it?")
            parent = userinput.ask_project(api)
        item.hibernate(parent)
        print("Action hibernated to {}".format(parent))

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

    def go_project():
        try:
            menu_project(api, item.get_project())
        except EOFError:
            print("Going back to item {}".format(item))

    print("In item {}".format(item))
    userinput.ask_menu(
        {'D': ('Set action to done (archive)', archive_item),
         'v': ('View action', view_item),
         'Del': ('Delete item', delete_item),
         'a': ('Activate action (move back from Someday/Maybe)',
               activate_item),
         'h': ('Hibernate item (Someday/Maybe)', hibernate_item),
         'm': ('Move item to another project', move_item),
         'd': ('Set due date', set_date),
         'e': ('Edit description', set_description),
         'l': ('Set labels', set_labels),
         'n': ('Create new note', add_note),
         'p': ('Set priority', set_priority),
         # Navigation
         'Gn': ('Go to a note to edit (EDITOR?)', edit_note),
         'Gp': ("Go to item's project", go_project),
         },
        prompt="What to do?")
    api.force_commit()
