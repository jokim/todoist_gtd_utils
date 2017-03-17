#!/bin/env python
# -*- encoding: utf-8 -*-

"""Utility functions for utility project."""

import argparse

def ask_confirmation(prompt, interactive=True):
    """Return True if user confirms prompt"""
    if not interactive:
        return True
    ret = raw_input(unicode(prompt + u" (y/N): ").encode('utf8'))
    return ret == 'y'

def get_argparser(*args, **kwargs):
    """Init an argparser with default functionality"""
    p = argparse.ArgumentParser(*args, **kwargs)
    p.add_argument('--configfile', help="Change path to config file",
                   default='~/.todoist_gtd_utils.ini')
    p.add_argument('--token', help="API token to user for user")
    return p
