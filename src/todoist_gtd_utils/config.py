#!/bin/env python
# -*- encoding: utf-8 -*-

""" Functionality for supporting configuration.

TODO:
- Switch to a saner config tool than ConfigParser! yaml-something?
- Verify config at startup

"""

from __future__ import unicode_literals

import sys
import os
# import codecs
import ConfigParser

""" Default files to get config from """
default_files = [u'~/.todoist_gtd_utils.ini']

""" The default settings that is used in config """
default_settings = {
        'todoist': {
            'api-token': None,
            },
        'gtd': {
            'target-projects': "GTD",
            'activate-before-due-date': 0,
            },
        'cleanup': {
            'ignore-labels': None,
            },
        }


class Config(ConfigParser.ConfigParser, object):
    """ Config settings for todoist_gtd_utils.

    Set default values.

    """

    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)
        self.fill_defaults(default_settings)
        # for f in default_files:
        #     fp = codecs.open(os.path.expanduser(f), encoding='utf8')
        #     self.readfp(fp)
        self.read(os.path.expanduser(f) for f in default_files)

    def fill_defaults(self, defaults):
        """Populate config with given default values.

        Used before reading input from file.

        :type defaults: dict
        :param defaults:
            Deeper dict, where keys are sections, and sub dict contains default
            values for its options.

        """
        for sect, opts in defaults.iteritems():
            self.add_section(sect)
            for opt, value in opts.iteritems():
                self.set(sect, opt, value)

    def get(self, section, option):
        """Override for hacking in UTF8 encoding."""
        r = super(Config, self).get(section, option)
        if isinstance(r, str):
            return unicode(r, 'utf-8')
        return r

    def get_commalist(self, section, option, *args, **kwargs):
        """Get/parse a comma separated list as a native list"""
        raw = self.get(section, option, *args, **kwargs)
        ret = []
        if raw:
            for e in raw.split(','):
                e = e.strip()
                if e:
                    ret.append(e)
        return ret


if __name__ == '__main__':
    # Print out config settings. Defaults if not config is set up
    c = Config()
    c.write(sys.stdout)
