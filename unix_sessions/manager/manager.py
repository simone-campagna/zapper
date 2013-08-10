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
import imp
import glob
import getpass
import tempfile

from .errors import *
from ..session import *

class Manager(object):
    RC_DIR_NAME = '.unix-sessions'
    TEMP_DIR_PREFIX = 'unix-sessions'
    SESSIONS_DIR_NAME = 'sessions'
    SESSION_TYPE_TEMPORARY = 'temporary'
    SESSION_TYPE_PERSISTENT = 'persistent'
    SESSION_TYPES = [SESSION_TYPE_PERSISTENT, SESSION_TYPE_TEMPORARY]
    SESSION_INIT_FILE = ".session"
    SUITES_DIR_NAME = 'suites'
    CURRENT_SESSION_NAME_VARNAME = "UXS_CURRENT_SESSION"
    SUITES_DIR_VARNAME = "UXS_SUITE_DIR"
    def __init__(self):
        home_dir = os.path.expanduser('~')
        username = getpass.getuser()
        self.rc_dir = os.path.join(home_dir, self.RC_DIR_NAME)
        self.user_suites_dir = os.path.join(self.rc_dir, self.SUITES_DIR_NAME)
        tmpdir = os.environ.get("TMPDIR", "/tmp")
        self.tmp_dir = os.path.join(tmpdir, ".{0}-{1}".format(self.TEMP_DIR_PREFIX, username))
        self.persistent_sessions_dir = os.path.join(self.rc_dir, self.SESSIONS_DIR_NAME)
        self.temporary_sessions_dir = os.path.join(self.tmp_dir, self.SESSIONS_DIR_NAME)
        self.sessions_dir = {
            self.SESSION_TYPE_PERSISTENT : self.persistent_sessions_dir,
            self.SESSION_TYPE_TEMPORARY : self.temporary_sessions_dir,
        }
        for d in self.user_suites_dir, self.persistent_sessions_dir, self.temporary_sessions_dir:
            if not os.path.lexists(d):
                os.makedirs(d)
        self.load_suites()
        self.current_session_name = None
        self.current_session_type = None
        self.load_current_session()

    def _load_modules(self, module_dir):
        #print("+++", module_dir)
        modules = []
        for module_path in glob.glob(os.path.join(module_dir, '*.py')):
            modules.append(self._load_module(module_path))
        return modules

    def _load_module(self, module_path):
        module_dirname, module_basename = os.path.split(module_path)
        module_name = module_basename[:-3]
        #print("---", module_path, module_name)
        sys_path = [module_dirname]
        module_info = imp.find_module(module_name, sys_path)
        if module_info:
            module = imp.load_module(module_name, *module_info)
        return module

    def load_suites(self):
        uxs_suite_dir = os.environ.get(self.SUITES_DIR_VARNAME, "")
        self.uxs_suite_dirs = [self.user_suites_dir]
        self.uxs_suite_dirs.extend(uxs_suite_dir.split(':'))
        for suite_dir in self.uxs_suite_dirs:
            #print("===", suite_dir)
            self._load_modules(suite_dir)

    def load_current_session(self):
        current_session = os.environ.get(self.CURRENT_SESSION_NAME_VARNAME, None)
        if current_session:
            tnl = current_session.split(':', 1)
            if len(tnl) != 2:
                raise SessionLoadingError("inconsistent environment {0}={1!r}".format(self.CURRENT_SESSION_NAME_VARNAME, current_session))
            self.current_session_type = tnl[0]
            if not self.current_session_type in self.SESSION_TYPES:
                raise SessionLoadingError("inconsistent environment {0}={1!r}: invalid session type {2}".format(
                    self.CURRENT_SESSION_NAME_VARNAME, current_session, self.current_session_type))
            self.current_session_name = tnl[1]
            try:
                self.load_session(self.current_session_name, self.current_session_type)
            except SessionError as e:
                raise SessionLoadingError("inconsistent environment {0}={1!r}: {2}".format(
                    self.CURRENT_SESSION_NAME_VARNAME, current_session, e))

    def acquire_session_dir(self, session_type, session_name, session_dir):
        with open(os.path.join(session_dir, self.SESSION_INIT_FILE), "w") as f_out:
            f_out.write("session_name = {0!r}\n".format(session_name))
            f_out.write("session_type = {0!r}\n".format(session_type))

    def create(self, session_name=None):
        session_type = None
        if session_name is None:
            session_type = self.SESSION_TYPE_TEMPORARY
            session_dir = tempfile.mkdtemp(dir=self.temporary_sessions_dir)
            session_name = os.path.basename(session_dir)
        else:
            session_type = self.SESSION_TYPE_PERSISTENT
            session_dir = os.path.join(self.persistent_sessions_dir, session_name)
            if os.path.lexists(session_dir):
                raise SessionCreationError("cannot create session {0!r}, since it already exists".format(session_name))
            os.makedirs(session_dir)
        self.acquire_session_dir(session_type, session_name, session_dir)
        print("created {t} session {n} at {d}".format(t=session_type, n=session_name, d=session_dir))
        
    def list(self, temporary=True, persistent=True):
        dl = []
        if temporary:
            dl.append((self.SESSION_TYPE_TEMPORARY, self.temporary_sessions_dir))
        if persistent:
            dl.append((self.SESSION_TYPE_PERSISTENT, self.persistent_sessions_dir))
        for session_type, sessions_dir in dl:
            print("=== Available {t} sessions:".format(t=session_type))
            for entry in glob.glob(os.path.join(sessions_dir, '*', self.SESSION_INIT_FILE)):
                session_name = os.path.basename(os.path.dirname(entry))
                if session_name == self.current_session_name:
                    mark_current = '*'
                else:
                    mark_current = ' '
                print("  {0} {1}".format(mark_current, session_name))

    def load_session(self, session_name, session_type=None):
        if session_type is None:
            session_types = self.SESSION_TYPES
        else:
            assert session_type in self.SESSION_TYPES
            session_types = [session_type]
        for session_type in session_types:
            sessions_dir = self.sessions_dir[session_type]
            session_dir = os.path.join(sessions_dir, session_name)
            if os.path.isdir(session_dir) and os.path.lexists(os.path.join(session_dir, self.SESSION_INIT_FILE)):
                self.current_session = Session(session_name, session_type)
                break
        else:
            raise SessionLoadingError("cannot load {t} session {n!r}".format(t=session_type, n=session_name))

    def info(self):
        print(self.current_session)

#def _run(method_name, *p_args, **n_args):
#    manager = Manager()
#    return getattr(manager, method_name)(*p_args, **n_args)
#
#def list(*p_args, **n_args):
#    return _run('list', *p_args, **n_args)
#
#def info(*p_args, **n_args):
#    return _run('info', *p_args, **n_args)
