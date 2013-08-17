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
from .package import Package
from .serializer import Serializer
from .serializers import *
from .utils.home import get_home_dir

class Manager(object):
    RC_DIR_NAME = '.unix-sessions'
    TEMP_DIR_PREFIX = 'unix-sessions'
    SESSIONS_DIR_NAME = 'sessions'
    SESSION_TYPE_TEMPORARY = 'temporary'
    SESSION_TYPE_PERSISTENT = 'persistent'
    SESSION_TYPES = [SESSION_TYPE_PERSISTENT, SESSION_TYPE_TEMPORARY]
    PACKAGES_DIR_NAME = 'packages'
    LOADED_PACKAGES_VARNAME = "UXS_LOADED_PACKAGES"
    TMP_PREFIX = "uxs_"
    def __init__(self):
        user_home_dir = os.path.expanduser('~')
        username = getpass.getuser()
        self.user_rc_dir = os.path.join(user_home_dir, self.RC_DIR_NAME)
        self.user_package_dir = os.path.join(self.user_rc_dir, self.PACKAGES_DIR_NAME)
        uxs_home_dir = get_home_dir()
        if uxs_home_dir and os.path.lexists(uxs_home_dir):
            uxs_etc_dir = os.path.join(uxs_home_dir, 'etc', 'unix-sessions')
            self.uxs_package_dir = os.path.join(uxs_etc_dir, self.PACKAGES_DIR_NAME)
        else:
            self.uxs_package_dir = None
        tmpdir = os.environ.get("TMPDIR", "/tmp")
        self.tmp_dir = os.path.join(tmpdir, ".{0}-{1}".format(self.TEMP_DIR_PREFIX, username))
        self.persistent_sessions_dir = os.path.join(self.user_rc_dir, self.SESSIONS_DIR_NAME)
        self.temporary_sessions_dir = os.path.join(self.tmp_dir, self.SESSIONS_DIR_NAME)
        self.sessions_dir = {
            self.SESSION_TYPE_PERSISTENT : self.persistent_sessions_dir,
            self.SESSION_TYPE_TEMPORARY : self.temporary_sessions_dir,
        }
        for d in self.user_package_dir, self.persistent_sessions_dir, self.temporary_sessions_dir:
            if not os.path.lexists(d):
                os.makedirs(d)
        self._session = None
        self.load_serialization()
        self.load_session()

    def get_session(self):
        return self._session

    def set_session(self, session):
        if self._session is not None:
            self.session.unload_packages()
            self.session.serialize(self.serializer)
        self._session = session

    session = property(get_session, set_session)

    def load_session(self, session_name=None):
        if session_name is None:
            session_dir = os.environ.get("UXS_SESSION", None)
            if session_dir:
                session_config_file = Session.get_session_config_file(session_dir)
                if not os.path.lexists(session_config_file):
                    LOGGER.warning("inconsistent environment: invalid session {0}".format(session_dir))
                    session_dir = None
            if session_dir is None:
                session_dir = tempfile.mkdtemp(dir=self.temporary_sessions_dir, prefix=self.TMP_PREFIX)
                Session.create_session_dir(manager=self, session_dir=session_dir, session_name=os.path.basename(session_dir), session_type='temporary')
        else:
            for sessions_dir in self.persistent_sessions_dir, self.temporary_sessions_dir:
                session_dir = os.path.join(sessions_dir, session_name)
                session_config_file = Session.get_session_config_file(session_dir)
                if os.path.lexists(session_config_file):
                    break
            else:
                raise SessionError("session {0} not found".format(session_name))
        try:
            if self.session:
                self.session.load(session_dir)
            else:
                self.session = Session(self, session_dir)
        except Exception as e:
            import traceback
            traceback.print_exc()
            del os.environ['UXS_SESSION']
            self.load_session()
                    
    def load_serialization(self):
        serialization = os.environ.get("UXS_SERIALIZATION", None)
        self.serialization_filename = None
        self.serializer = None
        if serialization is None:
            return
        l = serialization.split(':', 1)
        serialization_name = l[0]
        if len(l) == 1:
            self.serialization_filename = None
        else:
            self.serialization_filename = os.path.abspath(l[1])
        try:
            self.serializer = Serializer.createbyname(serialization_name)
        except Exception as e:
            raise SessionError("invalid serialization {0!r}: {1}: {2}".format(serialization_name, e.__class__.__name__, e))

    def create_session(self, session_name=None):
        session_type = None
        if session_name is None:
            session_type = self.SESSION_TYPE_TEMPORARY
            session_dir = tempfile.mkdtemp(dir=self.temporary_sessions_dir, prefix=self.TMP_PREFIX)
            session_name = os.path.basename(session_dir)
        else:
            session_type = self.SESSION_TYPE_PERSISTENT
            session_dir = os.path.join(self.persistent_sessions_dir, session_name)
            if os.path.lexists(session_dir):
                raise SessionCreationError("cannot create session {0!r}, since it already exists".format(session_name))
            os.makedirs(session_dir)
        Session.create_session_dir(manager=self, session_dir=session_dir, session_name=session_name, session_type=session_type)
        print("created {t} session {n} at {d}".format(t=session_type, n=session_name, d=session_dir))
        return session_dir

    def new_session(self, session_name=None):
        session_dir = self.create_session(session_name)
        self.session.load(session_dir)
        
    def delete_sessions(self, session_names):
        for session_name in session_names:
            self.delete_session(session_name)

    def delete_session(self, session_name_pattern):
        if session_name_pattern is None:
            session_name_pattern = self.session.session_name
        for session_dir in self.get_sessions(session_name_pattern):
            #print(self.session)
            if session_dir == self.session.session_dir:
                del os.environ['UXS_SESSION']
                self.load_session()
            #print(self.session)
            session_config_file = Session.get_session_config_file(session_dir)
            os.remove(session_config_file)
            try:
                os.rmdir(session_dir)
            except OSError:
                pass
        
    def get_sessions(self, session_name_pattern, temporary=True, persistent=True):
        dl = []
        if temporary:
            dl.append((self.SESSION_TYPE_TEMPORARY, self.temporary_sessions_dir))
        if persistent:
            dl.append((self.SESSION_TYPE_PERSISTENT, self.persistent_sessions_dir))
        session_dirs = []
        for session_type, sessions_dir in dl:
            for session_dir in glob.glob(os.path.join(sessions_dir, session_name_pattern)):
                session_config_file = Session.get_session_config_file(session_dir)
                if os.path.lexists(session_config_file):
                    session_dirs.append(session_dir)
        return session_dirs

    def get_session_dir(self, session_name, temporary=True, persistent=True):
        dl = []
        if temporary:
            dl.append((self.SESSION_TYPE_TEMPORARY, self.temporary_sessions_dir))
        if persistent:
            dl.append((self.SESSION_TYPE_PERSISTENT, self.persistent_sessions_dir))
        for session_type, sessions_dir in dl:
            session_dir = os.path.join(sessions_dir, session_name)
            session_config_file = Session.get_session_config_file(session_dir)
            if os.path.lexists(session_config_file):
                return session_dir
        return None

    def show_available_sessions(self, temporary=True, persistent=True):
        dl = []
        if temporary:
            dl.append((self.SESSION_TYPE_TEMPORARY, self.temporary_sessions_dir))
        if persistent:
            dl.append((self.SESSION_TYPE_PERSISTENT, self.persistent_sessions_dir))
        for session_type, sessions_dir in dl:
            print("=== Available {t} sessions:".format(t=session_type))
            session_dir_pattern = os.path.join(sessions_dir, '*')
            for entry in glob.glob(Session.get_session_config_file(session_dir_pattern)):

                session_name = os.path.basename(os.path.dirname(entry))
                if session_name == self.session.session_name:
                    mark_current = '*'
                else:
                    mark_current = ' '
                print("  {0} {1}".format(mark_current, session_name))

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

    def add_packages(self, package_labels):
        self.session.add(package_labels)

    def remove_packages(self, package_labels):
        self.session.remove(package_labels)

    def add_package_directories(self, package_directories):
        self.session.add_directories(package_directories)

    def remove_package_directories(self, package_directories):
        self.session.remove_directories(package_directories)

    def apply(self, serializer=None, serialization_filename=None):
        pass

    def revert(self, serializer=None, serialization_filename=None):
        pass

    def serialize(self, serializer=None, serialization_filename=None):
        if serializer is None:
            serializer = self.serializer
        if serialization_filename is None:
            serialization_filename = self.serialization_filename
        if serializer and serialization_filename:
            self.session.serialize_file(serializer, serialization_filename)
            
    def init(self, serializer=None, serialization_filename=None):
        environment = self.session.environment
        #print("UXS_SESSION={0}".format(environment.get('UXS_SESSION', None)))
        if not 'UXS_SESSION' in environment:
            environment['UXS_SESSION'] = self.session.session_dir
        #print(serializer, serialization_filename)
        if serializer:
            if serialization_filename:
                self.session.serialize_file(serializer, serialization_filename=os.path.abspath(serialization_filename))
            else:
                self.session.serialize_stream(serializer, stream=sys.stdout)
        

