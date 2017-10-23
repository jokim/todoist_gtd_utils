#!/bin/env python
# -*- encoding: utf8 -*-
#
# Copyright 2016 Joakim S. Hovlandsvåg
#
# This file is part of todoist_gtd_utils
#
# todoist_gtd_utils is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# todoist_gtd_utils is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# todoist_gtd_utils; if not, write to the Free Software Foundation, Inc., 59
# Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import io
from os.path import join
from os.path import dirname

from setuptools import setup
from setuptools import find_packages

def read(*filename, **kwargs):
    return io.open(
        join(dirname(__file__), *filename),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()

def get_requirements(filename):
    """ Read requirements from file. """
    with open(filename, 'r') as reqfile:
        for req_line in reqfile.readlines():
            req_line = req_line.strip()
            if req_line:
                yield req_line

setup(
    name='todoist_gtd_utils',
    version='0.2',
    description="Utility fixes for when forcing GTD in Todoist",
    long_description=read('README.rst'),
    url="https://github.com/jokim/todoist_gtd_utils",
    author="Joakim S. Hovlandsvåg",
    author_email="joakim.hovlandsvag@gmail.com",
    license="GPLv3",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    #py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    install_requires=list(get_requirements('requirements.txt')),
    scripts=[
        'bin/gtd_clean',
        'bin/gtd_utils',
        'bin/todoist_add_mail_item',
        ],
    include_package_data=True,
    zip_safe=False,
    #classifiers=[  http://pypi.python.org/pypi?%3Aaction=list_classifiers
    #keywords=[],
    #extra_require=[],
    )
