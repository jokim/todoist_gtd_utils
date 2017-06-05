Todoist GTD utils
=================

Simple utility script(s) for using Todoist as my GTD system, and mutt as my
e-mail client.

Setup
-----

The project is using standard `virtualenv` and `setup.py`. My setup for
development::

    cd todoist_gtd_utils/
    virtualenv env
    source env/bin/activate
    pip install -r requirements.txt
    python setup.py install

For testing, run `tox`.

For ease of use, add a config file::

    python todoist_gtd_utils/config.py > ~/.todoist_gtd_utils.ini
    # edit file with own settings
    vim ~/.todoist_gtd_utils.ini

Add a macro to mutt, for instance when pressing "GG"::

    macro index,pager GG "<pipe-entry>less > /tmp/mutt-$USER-mail-todoist.tmp<enter><shell-escape>~/src/todoist_gtd_utils/env/bin/python ~/src/todoist_gtd_utils/bin/todoist_add_mail_item /tmp/mutt-$USER-mail-todoist.tmp<enter>"


GTD workflow
------------

Following the GTD workflow for processing and organizing, this is the subset
that this project supports:

* "Stuff":

  - E-mail inbox: *N/A*, see `mutt` or other mail clients

  - Todoist Inbox: Not implemented anything around this, for now

  - Direct input to the CLI script: `bin/todoist_add_item`

* Not actionable:

  - Trash: *N/A*

  - Someday Maybe: Using a project "Someday Maybe" in Todoist

  - Reference: *N/A*, since Todoist is not for reference material. You *could*
    add an non-actionable item with a link to the support material, though
    (just start the description with a "*").

* Next actions:

  - Projects: Projects under a GTD project in Todoist, with items

  - Do it now: Item could be tagged with `@5min`

  - Delegate it: Not supported, put Todoist on BCC, and add label `@waiting`

  - Defer it:

    - Next actions: Items in Todoist, under (sub)project of GTD

    - Calendar: Set time to item, and Todoist updates the calendar
