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

import os
import re
import sys
import glob
import shutil
import getpass
import tempfile
import collections

from .errors import *
from .session import *
from .category import Category
from .package import Package
from .product import Product
from .package_expressions import ALL_EXPRESSIONS
from .translator import Translator
from .translators import *
from .host_config import HOST_CONFIG, HostConfig
from .user_config import USER_CONFIG, UserConfig
from .session_config import SESSION_CONFIG
from .expression import Expression
from .utils.install_data import get_home_dir, get_admin_user
from .utils.random_name import RandomNameSequence
from .utils.table import show_table, validate_format
from .utils.debug import PRINT
from .utils.trace import trace
from .utils.sort_keys import SortKeys
from .utils.strings import string_to_bool, bool_to_string, string_to_list, list_to_string

def _expression(s):
    if s is None:
        return None
    return eval(s, ALL_EXPRESSIONS, {})

def _bool(s):
    return string_to_bool(s)

def _list(s):
    return s

def _expand(s):
    return os.path.expanduser(os.path.expandvars(s))

class Manager(object):
    RC_DIR_NAME = '.zapper'
    TEMP_DIR_PREFIX = 'zapper'
    TMPDIR = os.environ.get("TMPDIR", "/tmp")
    USER = getpass.getuser()
    ADMIN_USER = get_admin_user()
    USER_HOME_DIR = os.path.expanduser('~')
    USER_RC_DIR = os.path.join(USER_HOME_DIR, RC_DIR_NAME)
    USER_TEMP_DIR = os.path.join(TMPDIR, "{0}-{1}".format(TEMP_DIR_PREFIX, USER))

    SESSIONS_DIR_NAME = 'sessions'
    PACKAGES_DIR_NAME = 'packages'

    PERSISTENT_SESSIONS_DIR = os.path.join(USER_RC_DIR, SESSIONS_DIR_NAME)
    TEMPORARY_SESSIONS_DIR = os.path.join(USER_TEMP_DIR, SESSIONS_DIR_NAME)

    SESSIONS_DIR = {
        Session.SESSION_TYPE_PERSISTENT : PERSISTENT_SESSIONS_DIR,
        Session.SESSION_TYPE_TEMPORARY : TEMPORARY_SESSIONS_DIR,
    }

    LOADED_PACKAGES_VARNAME = "ZAPPER_LOADED_PACKAGES"
    USER_CONFIG_FILE = 'user.config'
    DEFAULT_SESSION_FORMAT = '{__ordinal__:>3d}) {is_current} {type} {name} {description}'
    DEFAULT_SESSION_LAST = '<last>'
    DEFAULT_SESSION_NEW = '<new>'
    DEFAULT_SESSION_DICT = {
        DEFAULT_SESSION_NEW:  'use a new session',
        DEFAULT_SESSION_LAST: 'use last session',
    }
    SESSION_HEADER_DICT = collections.OrderedDict((
        ('__ordinal__', '#'),
        ('is_current',  'C'),
        ('type',        'TYPE'),
        ('name',        'NAME'),
        ('root',        'ROOT'),
        ('description', 'DESCRIPTION'),
    ))
    DEFAULT_SESSION_SORT_KEYS = SortKeys('', SESSION_HEADER_DICT, 'session')
    DEFAULT_CONFIG = collections.OrderedDict((
        ('quiet', False),
        ('verbose', False),
        ('debug', False),
        ('trace', False),
        ('subpackages', False),
        ('directories', ''),
        ('persistent_sessions_dir', PERSISTENT_SESSIONS_DIR),
        ('temporary_sessions_dir', TEMPORARY_SESSIONS_DIR),
        ('available_package_format', Session.AVAILABLE_PACKAGE_FORMAT),
        ('loaded_package_format', Session.LOADED_PACKAGE_FORMAT),
        ('available_session_format', DEFAULT_SESSION_FORMAT),
        ('package_dir_format', Session.PACKAGE_DIR_FORMAT),
        ('package_sort_keys', Session.DEFAULT_PACKAGE_SORT_KEYS),
        ('package_dir_sort_keys', Session.DEFAULT_PACKAGE_DIR_SORT_KEYS),
        ('session_sort_keys', DEFAULT_SESSION_SORT_KEYS),
        ('resolution_level', 0),
        ('filter_packages', None),
        ('show_header', True),
        ('show_header_if_empty', False),
        ('show_translation', False),
        ('default_session', DEFAULT_SESSION_LAST),
        ('default_packages', []),
        ('description', ''),
        ('read_only', False),
    ))
    DEFAULT_CONFIG_TYPE = dict(
        quiet=_bool,
        verbose=_bool,
        debug=_bool,
        trace=_bool,
        subpackages=_bool,
        directories=_list,
        persistent_sessions_dir=str,
        temporary_sessions_dir=str,
        available_package_format=Session.PackageFormat,
        loaded_package_format=Session.PackageFormat,
        available_session_format=str,
        package_dir_format=Session.PackageDirFormat,
        package_sort_keys=str,
        package_dir_sort_keys=str,
        session_sort_keys=str,
        resolution_level=int,
        filter_packages=_expression,
        show_header=_bool,
        show_header_if_empty=_bool,
        show_translation=_bool,
        default_session=str,
        default_packages=_list,
        description=str,
        read_only=_bool,
    )
    DEFAULT_CONFIG_CHECKERS = dict(
        session=dict(
            directories='CHECK_session_directories',
        )
    )
    EXPAND_KEYS = {'directories'}
    DEFAULT_LABEL = '<default>'
    CURRENT_LABEL = '<current>'
    LABEL_CONFIG = {
        'host':         HOST_CONFIG,
        'user':         USER_CONFIG,
        'session':      SESSION_CONFIG,
        DEFAULT_LABEL:  DEFAULT_CONFIG,
        CURRENT_LABEL:  DEFAULT_CONFIG,
    }
    RE_VALID_SESSION = re.compile("[a-zA-Z_][a-zA-Z_0-9]+")
    def __init__(self):
        self.user_package_dir = os.path.join(self.USER_RC_DIR, self.PACKAGES_DIR_NAME)
        zapper_home_dir = get_home_dir()
        if zapper_home_dir and os.path.lexists(zapper_home_dir):
            host_etc_dir = os.path.join(zapper_home_dir, 'etc', 'zapper')
            self.host_package_dir = os.path.join(host_etc_dir, self.PACKAGES_DIR_NAME)
            host_config_file = os.path.join(host_etc_dir, 'host.config')
            self.host_config = HostConfig(host_config_file)
        else:
            self.host_package_dir = None
            self.host_config = HostConfig()
        #tmpdir = os.environ.get("TMPDIR", "/tmp")
        #self.persistent_sessions_dir = os.path.join(self.USER_RC_DIR, self.SESSIONS_DIR_NAME)
        #self.temporary_sessions_dir = os.path.join(self.tmp_dir, self.SESSIONS_DIR_NAME)

        user_config_file = os.path.join(self.USER_RC_DIR, self.USER_CONFIG_FILE)
        self.user_config = UserConfig(user_config_file)

        self._dry_run = False
        self._force = False

        self._available_package_format = None
        self._loaded_package_format = None
        self._available_session_format = None
        self._package_format = None
        self._package_dir_format = None
        self._show_header = True
        self._show_header_if_empty = False
        self._show_translation = True

        self._package_sort_keys = None
        self._package_dir_sort_keys = None
        self._set_session_sort_keys = None

        self.load_general()

        self.load_user_config()
        if not self.host_config['config']['directories']:
            dirs = filter(lambda x: x is not None, [self.host_package_dir, self.user_package_dir])
            self.host_config['config']['directories'] = list_to_string(dirs)

        self.persistent_sessions_dir = self.get_config_key('persistent_sessions_dir')
        self.temporary_sessions_dir = self.get_config_key('temporary_sessions_dir')
        #print("persistent_sessions_dir={!r}, temporary_sessions_dir={!r}".format(self.persistent_sessions_dir, self.temporary_sessions_dir))
        for d in self.user_package_dir, self.persistent_sessions_dir, self.temporary_sessions_dir:
            if not os.path.lexists(d):
                os.makedirs(d)

        self._session = None
        self.package_options = {}
        self.package_options_from = {}
        self.load_user_package_option('version_defaults')

        self.load_translator()
        #self.restore_session()

    @classmethod
    def PackageSortKeys(cls, package_sort_keys):
        return Session.PackageSortKeys(package_sort_keys)

    @classmethod
    def PackageDirSortKeys(cls, package_dir_sort_keys):
        return Session.PackageDirSortKeys(package_dir_sort_keys)

    @classmethod
    def SessionSortKeys(cls, session_sort_keys):
        return SortKeys(session_sort_keys, cls.SESSION_HEADER_DICT, 'session')

    @classmethod
    def PackageFormat(cls, package_format):
        return Session.PackageFormat(package_format)

    @classmethod
    def PackageDirFormat(cls, package_dir_format):
        return Session.PackageDirFormat(package_dir_format)

    @classmethod
    def SessionFormat(cls, session_format):
        if session_format is not None:
            validate_format(session_format, **cls.SESSION_HEADER_DICT)
        return session_format

    @classmethod
    def SessionName(cls, session_name):
        if not cls.RE_VALID_SESSION.match(session_name):
            raise ValueError("invalid session name {!r}".format(session_name))
        #invalid_chars = set(session_name).intersection(cls.SESSION_NAME_INVALID_CHARS)
        #if invalid_chars:
        #    raise SessionError("invalid session name {!r}: invalid chars {!r}".format(session_name, ''.join(invalid_chars)))
        return session_name

    @classmethod
    def DefaultSession(cls, session_name):
        if session_name in cls.DEFAULT_SESSION_DICT:
            return session_name
        else:
            return cls.SessionName(session_name)

    def update_session(self):
        pass

    def set_dry_run(self, dry_run):
        self._dry_run = bool(dry_run)

    def set_force(self, force):
        self._force = bool(force)

    def set_show_header(self, show_header, show_header_if_empty):
        self._show_header = show_header
        self._show_header_if_empty = show_header_if_empty

    def set_show_translation(self, show_translation):
        self._show_translation = show_translation

    def set_package_sort_keys(self, sort_keys):
        if sort_keys is None:
            sort_keys = self.PackageSortKeys(self.get_config_key('package_sort_keys'))
        self._package_sort_keys = sort_keys

    def set_package_dir_sort_keys(self, sort_keys):
        if sort_keys is None:
            sort_keys = self.PackageDirSortKeys(self.get_config_key('package_dir_sort_keys'))
        self._package_dir_sort_keys = sort_keys

    def set_session_sort_keys(self, sort_keys):
        if sort_keys is None:
            sort_keys = self.SessionSortKeys(self.get_config_key('session_sort_keys'))
        if not sort_keys:
            sort_keys = self.DEFAULT_SESSION_SORT_KEYS
        self._session_sort_keys = sort_keys

    def get_session_sort_keys(self):
        if not self._session_sort_keys:
            return self.DEFAULT_SESSION_SORT_KEYS
        else:
            return self._session_sort_keys

    @classmethod
    def is_admin(cls):
        return cls.USER == cls.ADMIN_USER

    def set_package_format(self, value):
        self._package_format = Session.PackageFormat(value)

    def set_package_dir_format(self, value):
        self._package_dir_format = Session.PackageDirFormat(value)

    def load_general(self):
        # host categories:
        categories_s = self.host_config['general']['categories']
        if categories_s:
            categories = categories_s.split(':')
            Category.add_category(*categories)

        # user categories:
        categories_s = self.user_config['general']['categories']
        if categories_s:
            categories = categories_s.split(':')
            Category.add_category(*categories)
        
    def get_session(self):
        return self._session

    def set_session(self, session):
        if self._session is not None:
            self.session.unload_all_loaded_packages()
            self.session.translate(self.translator)
        self._session = session

    session = property(get_session, set_session)

    ### Package options
    def _update_package_option(self, option, label, from_package_option, package_option_dict, package_option_from_dict):
        assert isinstance(package_option_dict, dict)
        changed = False
        for key, value in from_package_option.items():
            key_changed = self._set_package_option_key(option, label, package_option_dict, key, value)
            if key_changed:
                package_option_from_dict[key] = label
            changed = changed or key_changed
        return changed

    def _set_generic_package_option_key(self, option, label, package_option, key, value):
        if package_option.get(key, None) != value:
            if label is not None:
                LOGGER.info("setting {0} {1} {1!r}={2!r}".format(label, option, key, value))
            package_option[key] = str(value)
            return True
        else:
            return False

    def _set_package_option_key(self, option, label, package_option_dict, key, value):
        assert isinstance(package_option_dict, dict)
        if str(package_option_dict.get(key, None)) != str(value):
            #if label is not None:
            #    LOGGER.debug("setting {0}[{1!r}] = {2!r}".format(label, key, value))
            package_option_dict[key] = value
            return True
        else:
            return False

    def show_package_option(self, option, label, package_option, keys, *, package_option_from=None):
        if not keys:
            keys = package_option.keys()
        if not isinstance(package_option, dict):
            # convert configparser.SectionProxies -> dict
            package_option_dict = {}
            package_option_from_dict = {}
            self._update_package_option(option, label, package_option, package_option_dict, package_option_from_dict)
            package_option = package_option_dict
        t = Table("{__ordinal__:>3d}) {from_label} {key} : {value}", show_header=self._show_header, show_header_if_empty=show_header_if_empty)
        t.set_column_title(from_label='FROM_CONFIG', key=option.upper())
        if package_option_from is None:
            package_option_from = {}
        for key in keys:
            if not key in package_option:
                LOGGER.error("no such package option {0}: {1}".format(option, key))
                continue
            value = package_option[key]
            from_label = package_option_from.get(key, label)
            t.add_row(from_label=from_label, key=key, value=repr(value))
        t.render(PRINT)
        #    lst.append((key, ':', repr(value)))
        #show_table("{0} {1}".format(label.title(), option), lst)
      
    def show_host_package_option(self, option, keys):
        return self.show_package_option(option, 'host', self.host_config[option], keys)

    def show_user_package_option(self, option, keys):
        return self.show_package_option(option, 'user', self.user_config[option], keys)

    def show_session_package_option(self, option, keys):
        return self.show_package_option(option, 'session', self.session_config[option], keys)

    def show_current_package_option(self, option, keys):
        return self.show_package_option(option, self.CURRENT_LABEL, self.package_options[option], keys, package_option_from=self.package_options_from[option])

    def _set_generic_package_option(self, option, label, package_option, key_values):
        changed = False
        for key_value in key_values:
            if not '=' in key_value:
                raise ValueError("{0}: invalid key=value pair {1!r}".format(label, key_value))
            key, value = key_value.split('=')
            changed = self._set_generic_package_option_key(option, label, package_option, key, value) or changed
        # check:
        package_option_dict = {}
        package_option_from_dict = {}
        self._update_package_option(option, label, package_option, package_option_dict, package_option_from_dict)
        return changed

    def set_host_package_option(self, option, key_values):
        if not self.is_admin():
            raise SessionAuthError("user {0}: not authorized to change host option {1}".format(self.USER, option))
        if self._set_generic_package_option(option, 'host', self.host_config[option], key_values) and not self._dry_run:
            self.host_config.store()

    def set_user_package_option(self, option, key_values):
        if self._set_generic_package_option(option, 'user', self.user_config[option], key_values) and not self._dry_run:
            self.user_config.store()

    def set_session_package_option(self, option, key_values):
        if self._set_generic_package_option(option, 'session', self.session_config[option], key_values) and not self._dry_run:
            self.session_config.store()

    def _reset_generic_package_option(self, option, label, package_option, keys):
        if not keys:
            keys = package_option.keys()
        changed = False
        for key in keys:
            if not key in package_option:
                LOGGER.warning("{0}: no such package option: {1}".format(label, key))
            else:
                del package_option[key]
                changed = True
        return changed

    def reset_host_package_option(self, option, keys):
        if not self.is_admin():
            raise SessionAuthError("user {0}: not authorized to change host option {1}".format(self.USER, option))
        if self._reset_generic_package_option(option, 'host', self.host_config[option], keys) and not self._dry_run:
            self.host_config.store()

    def reset_user_package_option(self, option, keys):
        if self._reset_generic_package_option(option, 'user', self.user_config[option], keys) and not self._dry_run:
            self.user_config.store()

    def reset_session_package_option(self, option, keys):
        if self._reset_generic_package_option(option, 'session', self.session_config[option], keys) and not self._dry_run:
            self.session_config.store()

    def load_user_package_option(self, option):
        host_package_option = self.host_config[option]
        user_package_option = self.user_config[option]
        self.package_options[option] = {}
        self.package_options_from[option] = {}
        for from_label, from_package_option in ('host', host_package_option), ('user', user_package_option):
            self._update_package_option(option, from_label, from_package_option, self.package_options[option], self.package_options_from[option])

    def load_session_package_option(self, option):
        session_package_option = self.session_config[option]
        self._update_package_option(option, 'session', session_package_option, self.package_options[option], self.package_options_from[option])

    ### Config
    @classmethod
    def iter_config_keys(cls, label):
        for key in cls.DEFAULT_CONFIG:
            if key in cls.LABEL_CONFIG[label]:
                yield key

    def _update_config(self, label, from_config, config_dict, config_from_dict):
        assert isinstance(config_dict, dict)
        changed = False
        for key in self.iter_config_keys(label):
            value = from_config.get(key, '')
            key_changed = False
            if value == '':
                if not key in config_dict:
                    config_dict[key] = ''
                    key_changed = True
            else:
                key_changed = self._set_config_key(label, config_dict, key, value)
            if key_changed:
                config_from_dict[key] = label
            changed = changed or key_changed
        return changed

    def _set_generic_config_key(self, label, config, key, action, value):
        current_value = config.get(key, None)
        key_type = self.DEFAULT_CONFIG_TYPE.get(key, str)
        if key in self.EXPAND_KEYS:
            value = _expand(value)
        if action == '=':
            new_value = value
        else:
            if action == '+=':
                add = True
            else:
                add = False
            if key_type in {int, float}:
                value = key_type(value)
                if not add:
                    value = - value
                if current_value:
                    new_value = key_type(current_value) + value
                else:
                    new_value = value
                new_value = str(new_value)
            elif key_type == _list:
                if current_value is None:
                    new_lst = []
                else:
                    new_lst = string_to_list(current_value)
                if not new_lst:
                    if add:
                        new_lst.append(value)
                else:
                    if add:
                        if not value in new_lst:
                            new_lst.append(value)
                    else:
                        #print(new_lst, value, value in new_lst)
                        if value in new_lst:
                            new_lst.remove(value)
                new_value = list_to_string(new_lst)
            else:
                LOGGER.error("unsupported {} for config key {}".format(action, key))
        if new_value != current_value:
            checkers = self.DEFAULT_CONFIG_CHECKERS.get(label, {})
            if key in checkers:
                checker = getattr(self, checkers[key])
                if not checker(label, key, new_value):
                    LOGGER.error("cannot set {} config key {}={!r}".format(label, key, value))
                    return False
            if label is not None:
                if action == '=':
                    new_value_str = ""
                else:
                    new_value_str = " [{!r}]".format(new_value)
                LOGGER.info("setting {} config {}{}{!r}{}".format(label, key, action, value, new_value_str))
                #print(new_value, type(new_value))
            config[key] = new_value
            return True

    def _set_config_key(self, label, config_dict, key, s_value):
        assert isinstance(config_dict, dict)
        key_type = self.DEFAULT_CONFIG_TYPE.get(key, type)
        value = key_type(s_value)
        if str(config_dict.get(key, None)) != str(value):
            #if label is not None:
            #    LOGGER.debug("setting {0}[{1!r}] = {2!r}".format(label, key, value))
            config_dict[key] = value
            return True
        else:
            return False

    def CHECK_session_directories(self, label, key, value):
        return self.session.check_directories(value)

    def show_config(self, label, config, keys, *, config_from=None):
        if not keys:
            keys = list(self.iter_config_keys(label))
        if not isinstance(config, dict):
            # convert configparser.SectionProxies -> dict
            config_dict = {}
            config_from_dict = {}
            self._update_config(label, config, config_dict, config_from_dict)
            config = config_dict
        t = Table("{__ordinal__:>3d}) {from_label} {key} : {value}", show_header=self._show_header, show_header_if_empty=self._show_header_if_empty)
        t.set_column_title(from_label='FROM_CONFIG')

        for key in keys:
            if not key in config:
                LOGGER.error("no such key: {0}".format(key))
                continue
            s_value = config[key]
            if key in {'default_packages'}:
                value = list_to_string(s_value)
            else:
                value = s_value
            if config_from is None:
                from_label = label
            else:
                from_label = config_from.get(key, label)
            t.add_row(from_label=from_label, key=key, value=repr(value))
        t.render(PRINT)
     
    def show_host_config(self, keys):
        return self.show_config('host', self.host_config['config'], keys)

    def show_user_config(self, keys):
        return self.show_config('user', self.user_config['config'], keys)

    def show_session_config(self, keys):
        return self.show_config('session', self.session_config['config'], keys)

    def show_current_config(self, keys):
        return self.show_config(self.CURRENT_LABEL, self.config, keys, config_from=self.config_from)

    def _set_generic_config(self, label, config, key_values):
        changed = False
        for key_value in key_values:
            for action in '+=', '-=', '=':
                if action in key_value:
                    key, value = key_value.split(action, 1)
                    break
            else:
                raise ValueError("{0}: invalid key=value pair {1!r}".format(label, key_value))
            if not key in config:
                LOGGER.error("{0}: no such key: {1}".format(label, key))
                continue
            changed = self._set_generic_config_key(label, config, key, action, value) or changed
        # check:
        config_dict = {}
        config_from_dict = {}
        self._update_config(label, config, config_dict, config_from_dict)
        return changed

    def set_host_config(self, key_values):
        if not self.is_admin():
            raise SessionAuthError("user {0}: not authorized to change host config".format(self.USER))
        if self._set_generic_config('host', self.host_config['config'], key_values) and not self._dry_run:
            self.host_config.store()

    def set_user_config(self, key_values):
        if self._set_generic_config('user', self.user_config['config'], key_values) and not self._dry_run:
            self.user_config.store()

    def set_session_config(self, key_values):
        if self._set_generic_config('session', self.session_config['config'], key_values) and not self._dry_run:
            self.session_config.store()

    def _reset_generic_config(self, label, config, keys):
        if not keys:
            keys = list(self.iter_config_keys(label))
        changed = False
        for key in keys:
            if not key in config:
                LOGGER.error("{0}: no such key {1}".format(label, key))
            if config[key] != '':
                config[key] = ''
                changed = True
        return changed

    def reset_host_config(self, keys):
        if not self.is_admin():
            raise SessionAuthError("user {0}: not authorized to change host config".format(self.USER))
        if self._reset_generic_config('host', self.host_config['config'], keys) and not self._dry_run:
            self.host_config.store()

    def reset_user_config(self, keys):
        if self._reset_generic_config('user', self.user_config['config'], keys) and not self._dry_run:
            self.user_config.store()

    def reset_session_config(self, keys):
        if self._reset_generic_config('session', self.session_config['config'], keys) and not self._dry_run:
            self.session_config.store()

#    @classmethod
#    def _str2bool(cls, s):
#        return string_to_bool(s)
#
#    @classmethod
#    def _str2int(cls, s):
#        return int(s)
#
#    @classmethod
#    def _str2expression(cls, s):
#        return _expression(s)
#
#    @classmethod
#    def _bool2str(cls, b):
#        return bool_to_string(b)
#
#    @classmethod
#    def _int2str(cls, i):
#        return str(i)
#
#    @classmethod
#    def _expression2str(cls, expression):
#        return str(expression)

    def get_config_key(self, key):
        if not key in self.config:
             raise ValueError("invalid key {0!r}".format(key))
        value = self.config[key]
        LOGGER.debug("getting config key {}={!r} from {}".format(key, value, self.config_from.get(key, '...')))
        return value

    def get_config_key_from(self, key, from_list):
        if not key in self.DEFAULT_CONFIG:
            raise ValueError("invalid key {0!r}".format(key))
        current_value = ''
        current_config_name = ''
        for config_name in from_list:
            if config_name == self.DEFAULT_LABEL:
                config = self.DEFAULT_CONFIG
            elif config_name == 'host':
                config = self.host_config['config']
            elif config_name == 'user':
                config = self.user_config['config']
            elif config_name == 'session':
                config = self.session_config['config']
            else:
                raise ValueError("invalid config name {!r}".format(config_name))
            if key in config:
                value = config[key]
                if value or current_value == '':
                    current_value = value
                    current_config_name = config_name
        LOGGER.debug("getting config key {}={!r} from {}".format(key, current_value, current_config_name))
        return current_value
        
    def get_host_config_key(self, key):
        return self.get_config_key_from(key, (self.DEFAULT_LABEL, 'host'))

    def get_user_config_key(self, key):
        return self.get_config_key_from(key, (self.DEFAULT_LABEL, 'host', 'user'))

    def load_user_config(self):
        host_config = self.host_config['config']
        user_config = self.user_config['config']
        self.config = {}
        self.config_from = {}
        for from_label, from_config in (self.DEFAULT_LABEL, self.DEFAULT_CONFIG), ('host', host_config), ('user', user_config):
            self._update_config(from_label, from_config, self.config, self.config_from)

    def load_session_config(self):
        session_config = self.session_config['config']
        self._update_config('session', session_config, self.config, self.config_from)

    def restore_session(self):
        def _verify_session_root(session_type, session_root):
            if session_root:
                LOGGER.debug("trying to load {} session {}".format(session_type, session_root))
                session_config_file = Session.get_session_config_file(session_root)
                if not os.path.lexists(session_config_file):
                    LOGGER.warning("cannot restore {} session {} since it does not exist".format(session_type, session_root))
                    session_root = None
            return session_root
    
        self.session = None
        session_root = _verify_session_root(
            '$ZAPPER_SESSION',
            os.environ.get("ZAPPER_SESSION", None))
        if not session_root:
            default_session = self.get_config_key('default_session')
            if default_session == self.DEFAULT_SESSION_LAST:
                session_root = _verify_session_root(
                    'last used',
                    self.user_config['sessions']['last_session'])
            elif default_session == self.DEFAULT_SESSION_NEW:
                session_root = None
            else:
                session_root = _verify_session_root(
                    'default',
                    self.get_session_root(default_session))
#        if session_root:
#            session_config_file = Session.get_session_config_file(session_root)
#            if not os.path.lexists(session_config_file):
#                LOGGER.warning("cannot restore deleted session {0}".format(session_root))
#                session_root = None
        if session_root:
            try:
                session = Session(session_root)
            except Exception as e:
                trace()
                LOGGER.warning("cannot restore session {0}: {1}: {2}".format(session_root, e.__class__.__name__, e))
                session = None
            self.session = session
        if self.session is not None:
            self._init_session()
        
    def load_session(self, session_name):
        for sessions_dir in self.persistent_sessions_dir, self.temporary_sessions_dir:
            session_root = os.path.join(sessions_dir, session_name)
            session_config_file = Session.get_session_config_file(session_root)
            if os.path.lexists(session_config_file):
                self._load_session_root(session_root)
                break
        else:
            raise SessionError("session {0} not found".format(session_name))
        
    def _load_session_root(self, session_root):
        if self.session is None:
            self.session = Session(session_root)
        else:
            self.session.load(session_root)
        self._init_session()

    def _init_session(self):
        self.session_config = self.session.session_config
        self.load_session_config()
        self.load_session_package_option('version_defaults')
                    
    def load_translator(self):
        target_translator = os.environ.get("ZAPPER_TARGET_TRANSLATOR", None)
        self.translation_filename = None
        self.translator = None
        if target_translator is None:
            return
        l = target_translator.split(':', 1)
        self.translation_name = l[0]
        if len(l) == 1:
            self.translation_filename = None
        else:
            self.translation_filename = os.path.abspath(l[1])
        try:
            self.translator = Translator.createbyname(self.translation_name)
        except Exception as e:
            raise SessionError("invalid target translation {0!r}: {1}: {2}".format(self.translation_name, e.__class__.__name__, e))

    def create_session(self, session_name=None, description=''):
        session_type = None
        if session_name is None:
            session_type = Session.SESSION_TYPE_TEMPORARY
            session_root = Session.create_unique_session_root(self.temporary_sessions_dir)
            session_name = os.path.basename(session_root)
        else:
            session_type = Session.SESSION_TYPE_PERSISTENT
            session_root = os.path.join(self.persistent_sessions_dir, session_name)
            #if os.path.lexists(session_root):
            #    raise SessionCreationError("cannot create session {0!r}, since it already exists".format(session_name))
            #os.makedirs(session_root)
        default_packages = string_to_list(self.get_config_key('default_packages'))
        Session.create_session_config(
            manager=self, session_root=session_root,
            session_name=session_name,
            session_type=session_type,
            session_description=description,
            session_packages=default_packages)
        PRINT("created {t} session {n} at {r}".format(t=session_type, n=session_name, r=session_root))
        return session_root

    def new_session(self, session_name=None, description=''):
        session_root = self.create_session(session_name=session_name, description=description)
        self._load_session_root(session_root)
        
    def delete_sessions(self, session_name):
        if isinstance(session_name, str):
            session_names = [session_name]
        else:
            session_names = session_name
        if not session_names:
            session_names = [self.session.session_name]
        for session_name in session_names:
            self.delete_session(session_name)

    def copy_sessions(self, session_name):
        if isinstance(session_name, str):
            session_names = [session_name]
        else:
            session_names = session_name
        if len(session_names) == 1:
            source_session_name = self.session.session_name
        else:
            source_session_name = session_names.pop(0)
        target_session_names = session_names
        source_session_root = self.get_session_root(source_session_name)
        if source_session_root is None:
            LOGGER.error("session {0} does not exist".format(source_session_name))
        for target_session_name in target_session_names:
            target_session_root = self._get_session_root(target_session_name, temporary=False, _check='mustnt_exist')
            if target_session_root is None:
                LOGGER.error("session {0} already exists".format(target_session_name))
            else:
                Session.copy(source_session_root, target_session_root)

    def delete_session(self, session_name_pattern):
        if session_name_pattern is None:
            session_name_pattern = self.session.session_name
        for session_root in self.get_sessions(session_name_pattern):
            if session_root == self.session.session_root:
                LOGGER.warning("you are deleting the current session {0}".format(self.session.session_name))
                self.session.delete()
            else:
                Session.delete_session_root(session_root)
        
    def get_sessions(self, session_name_pattern, temporary=True, persistent=True):
        dl = []
        if temporary:
            dl.append((Session.SESSION_TYPE_TEMPORARY, self.temporary_sessions_dir))
        if persistent:
            dl.append((Session.SESSION_TYPE_PERSISTENT, self.persistent_sessions_dir))
        session_roots = []
        for session_type, sessions_dir in dl:
            session_roots.extend(Session.get_session_roots(sessions_dir, session_name_pattern))
        return session_roots

    def get_session_root(self, session_name, temporary=True, persistent=True):
        return self._get_session_root(session_name=session_name, temporary=temporary, persistent=persistent, _check='must_exist')

    def _get_session_root(self, session_name, temporary=True, persistent=True, _check='must_exist'):
        dl = []
        if persistent:
            dl.append((Session.SESSION_TYPE_PERSISTENT, self.persistent_sessions_dir))
        if temporary:
            dl.append((Session.SESSION_TYPE_TEMPORARY, self.temporary_sessions_dir))
        for session_type, sessions_dir in dl:
            session_root = os.path.join(sessions_dir, session_name)
            session_config_file = Session.get_session_config_file(session_root)
            exists = os.path.lexists(session_config_file)
            if _check == 'must_exist' and not exists:
                continue
            elif _check == 'mustnt_exist' and exists:
                continue
            else:
                return session_root
        return None

    def set_session_format(self, session_format):
        self._session_format = self.SessionFormat(session_format)

    def get_available_session_format(self):
        session_format = self._session_format
        if not session_format:
            session_format = self.get_config_key('available_session_format')
        if not session_format:
            session_format = self.DEFAULT_SESSION_FORMAT
        return session_format

    def complete_available_sessions(self, temporary=True, persistent=True, *ignore_p_args, **ignore_n_args):
        sessions_dirs = []
        if temporary:
            sessions_dirs.append(self.temporary_sessions_dir)
        if persistent:
            sessions_dirs.append(self.persistent_sessions_dir)
        l = []
        for sessions_dir in sessions_dirs:
            session_root_pattern = os.path.join(sessions_dir, '*')
            for session_config_file in glob.glob(Session.get_session_config_file(session_root_pattern)):
                session_root = Session.get_session_root(session_config_file)
                session_name = os.path.basename(session_root)
                l.append(session_name)
        print(' '.join(l))

    def _complete_suite(self, suite, base, lst):
        if not isinstance(suite, Suite):
            return
        if base:
            prefix = base + Package.SUITE_SEPARATOR + suite.label
        else:
            prefix = suite.label
        for package in suite.packages():
            lst.append(prefix + Package.SUITE_SEPARATOR + package.label)
            self._complete_suite(package, prefix, lst)
        
    def _complete_packages(self, packages):
        lst = []
        for package in packages:
            #sys.stderr.write("package: {!r} ".format(package))
            lst.append(package.label)
            lst.append(package.absolute_label)
            self._complete_suite(package, '', lst)
        print(' '.join(lst))

    def complete_available_packages(self, *ignore_p_args, **ignore_n_args):
        self._complete_packages(self.session.available_packages())
        #print(' '.join(package.name for package in self.session.available_packages()))

    def complete_loaded_packages(self, *ignore_p_args, **ignore_n_args):
        self._complete_packages(self.session.loaded_packages())
        #print(' '.join(package.name for package in self.session.loaded_packages()))

    def complete_package_directories(self, *ignore_p_args, **ignore_n_args):
        print(' '.join(self.session.get_package_directories()))

    def complete_host_config_keys(self, *ignore_p_args, **ignore_n_args):
        print(' '.join(self.host_config['config'].keys()))

    def complete_user_config_keys(self, *ignore_p_args, **ignore_n_args):
        print(' '.join(self.user_config['config'].keys()))

    def complete_session_config_keys(self, *ignore_p_args, **ignore_n_args):
        print(' '.join(self.session_config['config'].keys()))

    def complete_config_keys(self, *ignore_p_args, **ignore_n_args):
        print(' '.join(self.config.keys()))

    def complete_product_names(self, *ignore_p_args, **ignore_n_args):
        print(' '.join(Product.get_product_names()))

    def complete_host_version_defaults(self, *ignore_p_args, **ignore_n_args):
        print(' '.join(self.host_config['version_defaults'].keys()))
            
    def complete_user_version_defaults(self, *ignore_p_args, **ignore_n_args):
        print(' '.join(self.user_config['version_defaults'].keys()))

    def complete_session_version_defaults(self, *ignore_p_args, **ignore_n_args):
        print(' '.join(self.session_config['version_defaults'].keys()))

    def complete_version_defaults(self, *ignore_p_args, **ignore_n_args):
        print(' '.join(self.package_options['version_defaults'].keys()))

    def show_available_sessions(self, temporary=True, persistent=True, sort_keys=None):
        if sort_keys is None:
            sort_keys = self.get_session_sort_keys()
        session_format = self.get_available_session_format()
        dl = []
        if temporary:
            dl.append((Session.SESSION_TYPE_TEMPORARY, self.temporary_sessions_dir))
        if persistent:
            dl.append((Session.SESSION_TYPE_PERSISTENT, self.persistent_sessions_dir))
        rows = []
        for session_type, sessions_dir in dl:
            session_root_pattern = os.path.join(sessions_dir, '*')
            for session_config_file in glob.glob(Session.get_session_config_file(session_root_pattern)):
                session_root = Session.get_session_root(session_config_file)
                session_name = os.path.basename(session_root)
                if session_name == self.session.session_name:
                    mark_current = '*'
                else:
                    mark_current = ' '
                description = self.get_config_key('description')
                rows.append(dict(name=session_name, type=session_type, root=session_root, is_current=mark_current,
                                 description=description))
        
        sort_keys.sort(rows)

        t = Table(session_format, show_header=self._show_header, show_header_if_empty=self._show_header_if_empty)
        for row_d in rows:
            t.add_row(**row_d)
        t.set_column_title(**self.SESSION_HEADER_DICT)
        t.render(PRINT)

    def show_defined_packages(self):
        self.session.show_defined_packages()

    def show_available_packages(self, package_labels):
        self.session.show_available_packages(package_labels)

    def show_loaded_packages(self):
        self.session.show_loaded_packages()

    def show_package(self, package_label):
        self.session.show_package(package_label)

    def session_info(self, session_name=None):
        if session_name is None:
            session = self.session
        else:
            session_root = self.get_session_root(session_name)
            if session_root is None or not os.path.lexists(Session.get_session_config_file(session_root)):
                LOGGER.error("session {!r} does not exists".format(session_name))
                return
            session = self.session.new_session(session_root)
        session.info()

    def load_package_labels(self, package_labels, resolution_level=0, subpackages=False, sticky=False, simulate=False):
        self.session.load_package_labels(package_labels, resolution_level=resolution_level, subpackages=subpackages, sticky=sticky, simulate=simulate)

    def unload_package_labels(self, package_labels, resolution_level=0, subpackages=False, sticky=False, simulate=False):
        self.session.unload_package_labels(package_labels, resolution_level=resolution_level, subpackages=subpackages, sticky=sticky, simulate=simulate)

    def clear_packages(self, sticky=False, simulate=False):
        self.session.clear(sticky=sticky, simulate=simulate)

    def apply(self, translator=None, translation_filename=None):
        pass

    def revert(self, translator=None, translation_filename=None):
        pass

    def initialize(self):
        if not self.session:
            if self._dry_run:
                return
            else:
                self.new_session()

        self.session.set_dry_run(self._dry_run)
        self.session.set_force(self._force)

        self.session.set_package_formats(
            available=self.get_config_key('available_package_format'),
            loaded=self.get_config_key('loaded_package_format'))

        package_format = self._package_format
        self.session.set_package_formatting(self._package_format)

        package_dir_format = self._package_dir_format
        if package_dir_format is None:
            package_dir_format = self.get_config_key('package_dir_format')
        self.session.set_package_dir_format(package_dir_format)

        self.session.set_package_sort_keys(self._package_sort_keys)
        self.session.set_package_dir_sort_keys(self._package_dir_sort_keys)

        self.session.set_show_header(self._show_header, self._show_header_if_empty)

        filter_packages = self.config['filter_packages']
        if isinstance(filter_packages, Expression):
            self.session.filter_packages(self.config['filter_packages'])
        self.session.set_version_defaults(self.package_options['version_defaults'])

    def finalize(self):
        if self.session:
            self.session.finalize()
        self.user_config['sessions']['last_session'] = self.session.session_root
        if not self._dry_run:
            self.user_config.store()
        self.translate()

    def translate(self, translator=None, translation_filename=None):
        if translator is None:
            translator = self.translator
        if translation_filename is None:
            translation_filename = self.translation_filename
        if translator and translation_filename:
            self.session.translate_file(translator, translation_filename)
        if self._show_translation:
            translation_stream = sys.stdout
            trailer = "=" * 70 + '\n'
            translation_stream.write(trailer)
            self.session.translate_stream(translator, translation_stream, dry_run=False)
            translation_stream.write(trailer)
            
    def init(self, translator=None, translation_filename=None):
        environment = self.session.environment
        if not 'ZAPPER_SESSION' in environment:
            environment['ZAPPER_SESSION'] = self.session.session_root
        if translator:
            if translation_filename:
                self.session.translate_file(translator, translation_filename=os.path.abspath(translation_filename))
            else:
                self.session.translate_stream(translator, stream=sys.stdout)
