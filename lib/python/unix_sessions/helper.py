#!/usr/bin/env python3
#
# Copyright 2013 Simone Campagna
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

__author__ = 'Simone Campagna'

from .manager import Manager
from .session import Session
from .utils.debug import PRINT

class Helper(object):
    def __init__(self, manager):
        self.manager = manager

    @classmethod
    def _help_format(cls, format_dict):
        return """\
Available keys:
---------------
{0}
""".format('\n'.join(" * {key}".format(key=key) for key in format_dict))

    @classmethod
    def help_available_package_format(cls):
        PRINT("""\
Set the format used to show the list of available packages.
""" + cls._help_format(Session.PACKAGE_HEADER_DICT))

    @classmethod
    def help_loaded_package_format(cls):
        PRINT("""\
Set the format used to show the list of loaded packages.
""" + cls._help_format(Session.PACKAGE_HEADER_DICT))

    @classmethod
    def help_available_session_format(cls):
        PRINT("""\
Set the format used to show the list of available sessions.
""" + cls._help_format(Manager.SESSION_HEADER_DICT))

    @classmethod
    def help_package_dir_format(cls):
        PRINT("""\
Set the format used to show the list of package directories.
""" + cls._help_format(Session.PACKAGE_DIR_HEADER_DICT))

    @classmethod
    def _help_sort_keys(cls, label, example1, example2):
        return """\

Keys can be chained using ':'. For instance:
{label}={example1!r}

A '-' sign before the key reverses the sorting:
{label}={example1!r}

The sort key '__ordinal__' has no effect.

""".format(label=label, example1=example1, example2=example2)

    @classmethod
    def help_package_sort_keys(cls):
        PRINT("""\
Set the keys used to sort packages.
""" + cls._help_sort_keys(
        label='package_sort_keys',
        example1='category:product:version',
        example2='category:-product:version',
    ) + cls._help_format(Session.PACKAGE_HEADER_DICT))

    @classmethod
    def help_package_dir_sort_keys(cls):
        PRINT("""\
Set the keys used to sort package directories. 
""" + cls._help_sort_keys(
        label='package_dir_sort_keys',
        example1='package_dir',
        example2='-package_dir',
    ) + cls._help_format(Session.PACKAGE_DIR_HEADER_DICT))

    @classmethod
    def help_session_sort_keys(cls):
        PRINT("""\
Set the keys used to sort sessions.
""" + cls._help_sort_keys(
        label='session_sort_keys',
        example1='type:name',
        example2='type:-name',
    ) + cls._help_format(Manager.SESSION_HEADER_DICT))

    @classmethod
    def help_default_session(cls):
        d = Manager.DEFAULT_SESSION_DICT.copy()
        d['my_session'] = "load session named 'my_session'"
        PRINT("""\
Set the default session to be loaded when shelf is used in a
clean environment.

Available values are:
{}

""".format('\n'.join("{!r:16s}: {}".format(k, v) for k, v in d.items())))
