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
import getpass
import tempfile

from .errors import *

class Manager(object):
    RC_DIR_NAME = '.unix-sessions'
    TEMP_DIR_PREFIX = 'unix-sessions'
    SESSIONS_DIR_NAME = 'sessions'
    SESSION_TYPE_TEMPORARY = 'temporary'
    SESSION_TYPE_PERSISTENT = 'persistent'
    SESSION_INIT_FILE = ".session"
    def __init__(self):
        home_dir = os.path.expanduser('~')
        username = getpass.getuser()
        self.rc_dir = os.path.join(home_dir, self.RC_DIR_NAME)
        tmpdir = os.environ.get("TMPDIR", "/tmp")
        self.tmp_dir = os.path.join(tmpdir, ".{0}-{1}".format(self.TEMP_DIR_PREFIX, username))
        self.persistent_sessions_dir = os.path.join(self.rc_dir, self.SESSIONS_DIR_NAME)
        self.temporary_sessions_dir = os.path.join(self.tmp_dir, self.SESSIONS_DIR_NAME)
        for d in self.persistent_sessions_dir, self.temporary_sessions_dir:
            if not os.path.lexists(d):
                os.makedirs(d)

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
                print("  * {0}".format(session_name))

    def info(self):
        print("... info")

#def _run(method_name, *p_args, **n_args):
#    manager = Manager()
#    return getattr(manager, method_name)(*p_args, **n_args)
#
#def list(*p_args, **n_args):
#    return _run('list', *p_args, **n_args)
#
#def info(*p_args, **n_args):
#    return _run('info', *p_args, **n_args)
