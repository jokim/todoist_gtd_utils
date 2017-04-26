Todoist GTD utils
=================

Simple utility script(s) for fixing missing GTD functionality in Todoist.

Setup
-----

The project is using standard `virtualenv` and `setup.py`. My setup for
development::

    cd todoist_gtd_utils/
    virtualenv env
    source env/bin/activate
    pip install -r requirements.txt
    python setup.py install

For ease of use, add a config file::

    python todoist_gtd_utils/config.py > ~/.todoist_gtd_utils.ini
    # edit file with own settings
    vim ~/.todoist_gtd_utils.ini


Add a macro to mutt, for instance when pressing "GG"::

    macro index,pager GG "<pipe-entry>less > /tmp/mutt-$USER-mail-todoist.tmp<enter><shell-escape>~/src/todoist_gtd_utils/env/bin/python ~/src/todoist_gtd_utils/bin/todoist_add_mail_item /tmp/mutt-$USER-mail-todoist.tmp<enter>"

