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
import collections

from .errors import *
from .session import *
from .package import Package, Category
from .serializer import Serializer
from .serializers import *

class Manager(object):
    RC_DIR_NAME = '.unix-sessions'
    TEMP_DIR_PREFIX = 'unix-sessions'
    SESSIONS_DIR_NAME = 'sessions'
    SESSION_TYPE_TEMPORARY = 'temporary'
    SESSION_TYPE_PERSISTENT = 'persistent'
    SESSION_TYPES = [SESSION_TYPE_PERSISTENT, SESSION_TYPE_TEMPORARY]
    PACKAGES_DIR_NAME = 'packages'
    LOADED_PACKAGES_VARNAME = "UXS_LOADED_PACKAGES"
    def __init__(self):
        home_dir = os.path.expanduser('~')
        username = getpass.getuser()
        self.rc_dir = os.path.join(home_dir, self.RC_DIR_NAME)
        self.user_packages_dir = os.path.join(self.rc_dir, self.PACKAGES_DIR_NAME)
        tmpdir = os.environ.get("TMPDIR", "/tmp")
        self.tmp_dir = os.path.join(tmpdir, ".{0}-{1}".format(self.TEMP_DIR_PREFIX, username))
        self.persistent_sessions_dir = os.path.join(self.rc_dir, self.SESSIONS_DIR_NAME)
        self.temporary_sessions_dir = os.path.join(self.tmp_dir, self.SESSIONS_DIR_NAME)
        self.sessions_dir = {
            self.SESSION_TYPE_PERSISTENT : self.persistent_sessions_dir,
            self.SESSION_TYPE_TEMPORARY : self.temporary_sessions_dir,
        }
        for d in self.user_packages_dir, self.persistent_sessions_dir, self.temporary_sessions_dir:
            if not os.path.lexists(d):
                os.makedirs(d)
        self.load_available_packages()
        self.load_session()
        self.load_serialization()

    def load_session(self):
        session_dir = os.environ.get("UXS_SESSION", None)
        if session_dir is None:
            session_dir = tempfile.mkdtemp(dir=self.temporary_sessions_dir, prefix="uxs")
            self.session = Session.create(session_dir, session_name=os.path.basename(session_dir), session_type='temporary')
        else:
            self.session = Session(session_dir)

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

    def load_available_packages(self):
        uxs_package_dir = os.environ.get("UXS_PACKAGE_DIR", "")
        self.uxs_package_dirs = [self.user_packages_dir]
        self.uxs_package_dirs.extend(uxs_package_dir.split(':'))
        for package_dir in self.uxs_package_dirs:
            #print("===", package_dir)
            self._load_modules(package_dir)

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
        self.session = Session.create(session_dir=session_dir, session_name=session_name, session_type=session_type)
        print("created {t} session {n} at {d}".format(t=session_type, n=session_name, d=session_dir))
        
    def list(self, temporary=True, persistent=True):
        dl = []
        if temporary:
            dl.append((self.SESSION_TYPE_TEMPORARY, self.temporary_sessions_dir))
        if persistent:
            dl.append((self.SESSION_TYPE_PERSISTENT, self.persistent_sessions_dir))
        for session_type, sessions_dir in dl:
            print("=== Available {t} sessions:".format(t=session_type))
            for entry in glob.glob(os.path.join(sessions_dir, '*', Session.SESSION_CONFIG_FILE)):
                session_name = os.path.basename(os.path.dirname(entry))
                if session_name == self.session.session_name:
                    mark_current = '*'
                else:
                    mark_current = ' '
                print("  {0} {1}".format(mark_current, session_name))

    def show_packages(self, packages):
        if Category.__categories__:
            max_category_len = max(len(category) for category in Category.__categories__)
        else:
            max_category_len = 0
        fmt = "{{0:{np}d}} {{1:{lc}s}} {{2}}".format(np=len(str(len(packages) - 1)), lc=max_category_len)
        for package_index, package in enumerate(packages):
            print(fmt.format(package_index, package.category, package.label()))
     
    def show_available_packages(self):
        self.show_packages(Package.REGISTRY)

    def info(self):
        print(self.session)
        print("=== Session name: {0}".format(self.session.session_name))
        print("            dir:  {0}".format(self.session.session_dir))
        print("            type: {0}".format(self.session.session_type))
        print("=== Packages:")
        self.show_packages(self.session.packages())

    def add(self, package_labels):
        self.session.add(package_labels)

    def remove(self, package_labels):
        self.session.remove(package_labels)

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
            self.session.serialize(serializer, serialization_filename)
            
#    def _apply_or_revert(self, method_name, serializer=None, serialization_filename=None):
#        if serializer is None:
#            serializer = self.serializer
#        if serialization_filename is None:
#            serialization_filename = self.serialization_filename
#        for package in self.current_packages:
#            print("### {0} {1}...".format(method_name, package))
#            getattr(package, method_name)(self.session)
#           
#        environment = self.session.environment
#        orig_environment = self.session.orig_environment
#        #for key, val in environment.changeditems():
#        #    print("{0}: <{1!r}".format(key, orig_environment.get(key, None)))
#        #    print("{0}: >{1!r}".format(key, val))
#        if serializer and serialization_filename:
#            with open(serialization_filename, "w") as f_out:
#                self.session.serialize(serializer, stream=f_out, filename=os.path.abspath(serialization_filename))
#
#    def apply(self, serializer=None, serialization_filename=None):
#        self.session.environment[self.LOADED_PACKAGES_VARNAME] = ':'.join(package.label() for package in self.current_packages)
#        return self._apply_or_revert('apply', serializer, serialization_filename)
#
#    def revert(self, serializer=None, serialization_filename=None):
#        del self.session.environment[self.LOADED_PACKAGES_VARNAME]
#        return self._apply_or_revert('revert', serializer, serialization_filename)

    def init(self, serializer=None, serialization_filename=None):
        environment = self.session.environment
        print("UXS_SESSION={0}".format(environment.get('UXS_SESSION', None)))
        if not 'UXS_SESSION' in environment:
            environment['UXS_SESSION'] = self.session.session_dir
        print(serializer, serialization_filename)
        if serializer:
            if serialization_filename:
                with open(serialization_filename, "w") as f_out:
                    self.session.serialize(serializer, stream=f_out, filename=os.path.abspath(serialization_filename))
            else:
                self.session.serialize(serializer, stream=sys.stdout)
        

