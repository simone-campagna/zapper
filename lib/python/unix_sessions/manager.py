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
from .package_expressions import ALL_EXPRESSIONS
from .translator import Translator
from .translators import *
from .user_config import UserConfig
from .site_config import SiteConfig
from .expression import Expression
from .utils.home import get_home_dir
from .utils.random_name import RandomNameSequence
from .utils.show_table import show_table
from .utils.debug import PRINT
from .utils.trace import trace

class Manager(object):
    RC_DIR_NAME = '.unix-sessions'
    TEMP_DIR_PREFIX = 'unix-sessions'
    SESSIONS_DIR_NAME = 'sessions'
    PACKAGES_DIR_NAME = 'packages'
    LOADED_PACKAGES_VARNAME = "UXS_LOADED_PACKAGES"
    USER_CONFIG_FILE = 'user.config'
    MANAGER_DEFAULTS_KEYS = (
        'verbose',
        'debug',
        'trace',
        'subpackages',
        'resolution_level',
        'filter_packages',
    )
    MANAGER_DEFAULTS = {
        'verbose': False,
        'debug': False,
        'trace': False,
        'subpackages': False,
        'resolution_level': 0,
        'filter_packages': None,
    }
    def __init__(self):
        user_home_dir = os.path.expanduser('~')
        username = getpass.getuser()
        self.user_rc_dir = os.path.join(user_home_dir, self.RC_DIR_NAME)
        self.user_package_dir = os.path.join(self.user_rc_dir, self.PACKAGES_DIR_NAME)
        uxs_home_dir = get_home_dir()
        if uxs_home_dir and os.path.lexists(uxs_home_dir):
            uxs_etc_dir = os.path.join(uxs_home_dir, 'etc', 'unix-sessions')
            self.uxs_package_dir = os.path.join(uxs_etc_dir, self.PACKAGES_DIR_NAME)
            site_config_file = os.path.join(uxs_etc_dir, 'site.config')
            self.site_config = SiteConfig(site_config_file)
        else:
            self.uxs_package_dir = None
            self.site_config = SiteConfig()
        tmpdir = os.environ.get("TMPDIR", "/tmp")
        self.tmp_dir = os.path.join(tmpdir, ".{0}-{1}".format(self.TEMP_DIR_PREFIX, username))
        self.persistent_sessions_dir = os.path.join(self.user_rc_dir, self.SESSIONS_DIR_NAME)
        self.temporary_sessions_dir = os.path.join(self.tmp_dir, self.SESSIONS_DIR_NAME)
        self.sessions_dir = {
            Session.SESSION_TYPE_PERSISTENT : self.persistent_sessions_dir,
            Session.SESSION_TYPE_TEMPORARY : self.temporary_sessions_dir,
        }
        for d in self.user_package_dir, self.persistent_sessions_dir, self.temporary_sessions_dir:
            if not os.path.lexists(d):
                os.makedirs(d)
        self._session = None

        user_config_file = os.path.join(self.user_rc_dir, self.USER_CONFIG_FILE)
        self.user_config = UserConfig(user_config_file)

        self.load_general()

        self.load_user_defaults()

        self.load_translator()
        self.load_session()

    def load_general(self):
        # site categories:
        categories_s = self.site_config['general']['categories']
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
            self.session.unload_packages()
            self.session.translate(self.translator)
        self._session = session

    session = property(get_session, set_session)

    def show_defaults(self, label, defaults, keys):
        if not keys:
            keys = self.MANAGER_DEFAULTS_KEYS
        if not isinstance(defaults, dict):
            # convert configparser.SectionProxies -> dict
            defaults_dict = {}
            self._update_defaults(label, defaults, defaults_dict)
            defaults = defaults_dict
        lst = []
        for key in keys:
            if not key in defaults:
                LOGGER.error("no such key: {0}".format(key))
                continue
            value = defaults[key]
            lst.append((key, ':', repr(value)))
        show_table("{0} defaults".format(label.title()), lst, header=('KEY', '', 'VALUE'))
     
    def show_site_defaults(self, keys):
        return self.show_defaults('site', self.site_config['defaults'], keys)

    def show_user_defaults(self, keys):
        return self.show_defaults('user', self.user_config['defaults'], keys)

    def show_session_defaults(self, keys):
        return self.show_defaults('session', self.session_config['defaults'], keys)

    def show_current_defaults(self, keys):
        return self.show_defaults('current', self.defaults, keys)

    def _set_config_defaults(self, label, defaults, key_values):
        changed = False
        for key_value in key_values:
            if not '=' in key_value:
                raise ValueError("{0}: invalid key=value pair {1!r}".format(label, key_value))
            key, value = key_value.split('=')
            if not key in defaults:
                LOGGER.error("{0}: no such key: {1}".format(label, key))
                continue
            changed = self._set_config_default_key(label, defaults, key, value) or changed
        return changed

    def set_user_defaults(self, key_values):
        if self._set_config_defaults('user', self.user_config['defaults'], key_values):
            self.user_config.store()

    def set_session_defaults(self, key_values):
        if self._set_config_defaults('session', self.session_config['defaults'], key_values):
            self.session_config.store()

    def _unset_config_defaults(self, label, defaults, keys):
        if not keys:
            keys = self.MANAGER_DEFAULTS_KEYS
        changed = False
        for key in keys:
            if not key in defaults:
                LOGGER.error("{0}: no such key {1}".format(label, key))
            if defaults[key] != '':
                defaults[key] = ''
                changed = True
        return changed

    def unset_user_defaults(self, keys):
        if self._unset_config_defaults('user', self.user_config['defaults'], keys):
            self.user_config.store()

    def unset_session_defaults(self, keys):
        if self._unset_config_defaults('session', self.session_config['defaults'], keys):
            self.session_config.store()

    @classmethod
    def _str2bool(cls, s):
        try:
            i = int(s)
            return bool(i)
        except ValueError as e:
            pass
        if s.lower() in {'true', 'on'}:
            return True
        elif s.lower() in {'false', 'off'}:
            return False
        else:
            raise ValueError("invalid value {0!r} for bool".format(s))

    @classmethod
    def _str2int(cls, s):
        return int(s)

    @classmethod
    def _str2expression(cls, s):
        return eval(s, ALL_EXPRESSIONS, {})

    @classmethod
    def _bool2str(cls, b):
        return str(b)

    @classmethod
    def _int2str(cls, i):
        return str(i)

    @classmethod
    def _expression2str(cls, expression):
        return str(expression)

    def get_default_key(self, key):
        if not key in self.defaults:
             raise ValueError("invalid key {0!r}".format(key))
        return self.defaults[key]

    def load_user_defaults(self):
        site_defaults = self.user_config['defaults']
        user_defaults = self.user_config['defaults']
        self.defaults = {}
        for from_defaults in self.MANAGER_DEFAULTS, site_defaults, user_defaults:
            self._update_defaults('defaults', from_defaults, self.defaults)

    def _update_defaults(self, label, from_defaults, defaults_dict):
        assert isinstance(defaults_dict, dict)
        changed = False
        for key in self.MANAGER_DEFAULTS.keys():
            value = from_defaults.get(key, '')
            if value == '':
                if not key in defaults_dict:
                    defaults_dict[key] = ''
                    changed = True
            else:
                changed = self._set_default_key(label, defaults_dict, key, value) or changed
        return changed

    def _set_config_default_key(self, label, defaults, key, value):
        if defaults.get(key, None) != value:
            if label is not None:
                LOGGER.info("setting {0}[{1!r}] = {2!r}".format(label, key, value))
            defaults[key] = str(value)
            return True
        else:
            return False

    def _set_default_key(self, label, defaults_dict, key, s_value):
        assert isinstance(defaults_dict, dict)
        if key in {'verbose', 'debug', 'trace', 'subpackages'}:
            if isinstance(s_value, str):
                value = self._str2bool(s_value)
            else:
                value = s_value
                assert isinstance(s_value, bool)
        elif key in {'resolution_level'}:
            if isinstance(s_value, str):
                value = self._str2int(s_value)
            else:
                value = s_value
                assert isinstance(s_value, int)
        elif key in {'filter_packages'}:
            if isinstance(s_value, str):
                value = self._str2expression(s_value)
            else:
                value = s_value
                assert isinstance(value, Expression) or value is None
        if str(defaults_dict.get(key, None)) != str(value):
            #if label is not None:
            #    LOGGER.debug("setting {0}[{1!r}] = {2!r}".format(label, key, value))
            defaults_dict[key] = value
            return True
        else:
            return False

    def load_session_defaults(self):
        session_defaults = self.session_config['defaults']
        self._update_defaults('defaults', session_defaults, self.defaults)

#    def store_defaults(self):
#        defaults = self.user_config['defaults']
#        for key in {'verbose', 'debug', 'trace', 'subpackages'}:
#            defaults[key] = self._bool2str(self.defaults[key])
#        for key in {'resolution_level'}:
#            defaults[key] = self._int2str(self.defaults[key])

    def load_session(self, session_name=None):
        return self._load_session(session_name=None, _depth=0)

    def _load_session(self, session_name=None, _depth=0):
        if session_name is None:
            session_root = os.environ.get("UXS_SESSION", None)
            if session_root is None:
                session_root = self.user_config['sessions']['last_session']
            if session_root:
                session_config_file = Session.get_session_config_file(session_root)
                if not os.path.lexists(session_config_file):
                    LOGGER.warning("inconsistent environment: invalid session {0}".format(session_root))
                    session_root = None
            if session_root is None:
                session_root = Session.create_unique_session_root(self.temporary_sessions_dir)
                Session.create_session_config(manager=self, session_root=session_root, session_name=os.path.basename(session_root), session_type='temporary')
        else:
            for sessions_dir in self.persistent_sessions_dir, self.temporary_sessions_dir:
                session_root = os.path.join(sessions_dir, session_name)
                session_config_file = Session.get_session_config_file(session_root)
                if os.path.lexists(session_config_file):
                    break
            else:
                raise SessionError("session {0} not found".format(session_name))
        try:
            if self.session:
                self.session.load(session_root)
            else:
                self.session = Session(self, session_root)
        except SessionError as e:
            trace()
            os.environ.pop('UXS_SESSION', None)
            if _depth == 0:
                try:
                    self._load_session(session_name=None, _depth=_depth + 1)
                except Exception as e:
                    raise
            else:
                raise
        self.session_config = self.session.session_config
        self.load_session_defaults()
                    
    def load_translator(self):
        target_translator = os.environ.get("UXS_TARGET_TRANSLATOR", None)
        self.translation_filename = None
        self.translator = None
        if target_translator is None:
            return
        l = target_translator.split(':', 1)
        translation_name = l[0]
        if len(l) == 1:
            self.translation_filename = None
        else:
            self.translation_filename = os.path.abspath(l[1])
        try:
            self.translator = Translator.createbyname(translation_name)
        except Exception as e:
            raise SessionError("invalid target translation {0!r}: {1}: {2}".format(translation_name, e.__class__.__name__, e))

    def create_session(self, session_name=None):
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
        Session.create_session_config(manager=self, session_root=session_root, session_name=session_name, session_type=session_type)
        PRINT("created {t} session {n} at {r}".format(t=session_type, n=session_name, r=session_root))
        return session_root

    def new_session(self, session_name=None):
        session_root = self.create_session(session_name)
        self.session.load(session_root)
        
    def delete_sessions(self, session_names):
        for session_name in session_names:
            self.delete_session(session_name)

    def copy_sessions(self, session_names):
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
                LOGGER.warning("cannot delete current session {0}".format(self.session.session_name))
                continue
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

    def show_available_sessions(self, temporary=True, persistent=True):
        dl = []
        if temporary:
            dl.append((Session.SESSION_TYPE_TEMPORARY, self.temporary_sessions_dir))
        if persistent:
            dl.append((Session.SESSION_TYPE_PERSISTENT, self.persistent_sessions_dir))
        for session_type, sessions_dir in dl:
            table = []
            session_root_pattern = os.path.join(sessions_dir, '*')
            for session_config_file in glob.glob(Session.get_session_config_file(session_root_pattern)):
                session_root = Session.get_session_root(session_config_file)
                session_name = os.path.basename(session_root)
                if session_name == self.session.session_name:
                    mark_current = '*'
                else:
                    mark_current = ' '
                table.append((mark_current, session_name))
            title = "Available {t} sessions".format(t=session_type)
            show_table(title, table)

    def show_defined_packages(self):
        self.session.show_defined_packages()

    def show_available_packages(self):
        self.session.show_available_packages()

    def show_loaded_packages(self):
        self.session.show_loaded_packages()

    def show_package_directories(self):
        self.session.show_package_directories()

    def show_package(self, package_label):
        self.session.show_package(package_label)

    def info_session(self):
        self.session.info()

    def add_packages(self, package_labels, resolution_level=0, subpackages=False):
        self.session.add(package_labels, resolution_level=resolution_level, subpackages=subpackages)

    def remove_packages(self, package_labels, resolution_level=0, subpackages=False):
        self.session.remove(package_labels, resolution_level=resolution_level, subpackages=subpackages)

    def clear_packages(self):
        self.session.clear()

    def add_package_directories(self, package_directories):
        self.session.add_directories(package_directories)

    def remove_package_directories(self, package_directories):
        self.session.remove_directories(package_directories)

    def apply(self, translator=None, translation_filename=None):
        pass

    def revert(self, translator=None, translation_filename=None):
        pass

    def initialize(self):
        filter_packages = self.defaults['filter_packages']
        print(filter_packages, repr(filter_packages), type(filter_packages))
        if isinstance(filter_packages, Expression):
            self.session.filter_packages(self.defaults['filter_packages'])

    def finalize(self):
        self.user_config['sessions']['last_session'] = self.session.session_root
        self.user_config.store()
        self.translate()

    def translate(self, translator=None, translation_filename=None):
        if translator is None:
            translator = self.translator
        if translation_filename is None:
            translation_filename = self.translation_filename
        if translator and translation_filename:
            self.session.translate_file(translator, translation_filename)
            
    def init(self, translator=None, translation_filename=None):
        environment = self.session.environment
        if not 'UXS_SESSION' in environment:
            environment['UXS_SESSION'] = self.session.session_root
        if translator:
            if translation_filename:
                self.session.translate_file(translator, translation_filename=os.path.abspath(translation_filename))
            else:
                self.session.translate_stream(translator, stream=sys.stdout)
        

