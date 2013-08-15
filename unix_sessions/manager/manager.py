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
from ..session import *
from ..package import Package
from ..serializer import Serializer

Index = collections.namedtuple('Index', ('idx', 'path'))

class Manager(object):
    RC_DIR_NAME = '.unix-sessions'
    TEMP_DIR_PREFIX = 'unix-sessions'
    SESSIONS_DIR_NAME = 'sessions'
    SESSION_TYPE_TEMPORARY = 'temporary'
    SESSION_TYPE_PERSISTENT = 'persistent'
    SESSION_TYPES = [SESSION_TYPE_PERSISTENT, SESSION_TYPE_TEMPORARY]
    SESSION_INIT_FILE = ".session"
    PACKAGES_DIR_NAME = 'packages'
    CURRENT_SESSION_NAME_VARNAME = "UXS_CURRENT_SESSION"
    PACKAGES_DIR_VARNAME = "UXS_PACKAGE_DIR"
    SESSION_INDEX_VARNAME = "UXS_SESSION_INDEX"
    LOADED_PACKAGES_VARNAME = "UXS_LOADED_PACKAGES"
    CURRENT_SERIALIZATION_VARNAME ="UXS_CURRENT_SERIALIZATION"
    VERSION_OPERATORS = (
        ('==',		lambda x, v: x == v),
        ('!=',		lambda x, v: x != v),
        ('<',		lambda x, v: x <  v),
        ('<=',		lambda x, v: x <= v),
        ('>',		lambda x, v: x >  v),
        ('>=',		lambda x, v: x >= v),
    )
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
        self.current_session_name = None
        self.current_session_type = None
        self.current_session_dir = None
        self.current_packages = []
        self.load_current_session()
        self.load_current_serialization()

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
        uxs_package_dir = os.environ.get(self.PACKAGES_DIR_VARNAME, "")
        self.uxs_package_dirs = [self.user_packages_dir]
        self.uxs_package_dirs.extend(uxs_package_dir.split(':'))
        for package_dir in self.uxs_package_dirs:
            #print("===", package_dir)
            self._load_modules(package_dir)

    def load_current_session(self):
        current_session_index = os.environ.get(self.SESSION_INDEX_VARNAME, None)
        if current_session_index is None:
            self.current_session_index = 0
        else:
            try:
                self.current_session_index = int(current_session_index)
            except ValueError as e:
                raise SessionLoadingError("inconsistent environment {0}={1!r}".format(
                    self.SESSION_INDEX_VARNAME, current_session_index))
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

    def load_current_serialization(self):
        current_serialization = os.environ.get(self.CURRENT_SERIALIZATION_VARNAME, None)
        self.current_serialization_filename = None
        self.current_serializer = None
        if current_serialization is None:
            return
        l = current_serialization.split(':', 1)
        current_serialization_name = l[0]
        if len(l) == 1:
            self.current_serialization_filename = None
        else:
            self.current_serialization_filename = os.path.abspath(l[1])
        try:
            self.current_serializer = Serializer.createbyname(current_serialization_name)
        except Exception as e:
            raise SessionError("invalid serialization {0!r}: {1}: {2}".format(current_serialization_name, e.__class__.__name__, e))

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
                self.current_session_dir = session_dir
                self.load_session_packages()
                break
        else:
            raise SessionLoadingError("cannot load {t} session {n!r}".format(t=session_type, n=session_name))

    def load_session_packages(self):
        for index in self.get_session_indices():
            if index.idx >= self.current_session_index:
                with open(index.path, 'r') as f_in:
                    for line in f_in:
                        line = line.strip()
                        if line:
                            action, package_label = line.split(':', 1)
                            if action == 'add':
                                package_list = Package.REGISTRY
                                func = self.add_package
                                message = "available"
                            elif action == 'remove':
                                package_list = self.current_packages
                                func = self.remove_package
                                message = "loaded"
                            package = self.get_package(package_label, package_list)
                            if package is None:
                                raise PackageNotFoundError("package {0} not {1}".format(package_label, message))
                            func(package)
                self.current_session_index = index.idx

    def add_package(self, package):
        print("### add {0}".format(package.label()))
        if not package in self.current_packages:
            self.current_packages.append(package)

    def remove_package(self, package):
        print("### remove {0}".format(package.label()))
        if package in self.current_packages:
            self.current_packages.remove(package)

    def info(self):
        print(self.current_session)
        #print(self.current_session_dir)
        print("=== Session:")
        for index in self.get_session_indices():
            with open(index.path, 'r') as f_in:
                packages = list(line.strip() for line in f_in.readlines())
            if index.idx <= self.current_session_index:
                mark = '*'
            else:
                mark = ' '
            print(" {0} {1:3d}) {2}".format(mark, index.idx, ' '.join(packages)))
        print("=== Loaded packages:")
        for package in self.current_packages:
            print(" + {0}".format(package.label()))
        
    def _apply_or_revert(self, method_name, serializer=None, serialization_filename=None):
        if serializer is None:
            serializer = self.current_serializer
        if serialization_filename is None:
            serialization_filename = self.current_serialization_filename
        #print(self.current_session, serializer, serialization_filename)
        for package in self.current_packages:
            print("### {0} {1}...".format(method_name, package))
            getattr(package, method_name)(self.current_session)
           
        environment = self.current_session.environment
        orig_environment = self.current_session.orig_environment
        #for key, val in environment.changeditems():
        #    print("{0}: <{1!r}".format(key, orig_environment.get(key, None)))
        #    print("{0}: >{1!r}".format(key, val))
        if serializer and serialization_filename:
            with open(serialization_filename, "w") as f_out:
                self.current_session.serialize(serializer, stream=f_out, filename=os.path.abspath(serialization_filename))

    def apply(self, serializer=None, serialization_filename=None):
        self.current_session.environment[self.LOADED_PACKAGES_VARNAME] = ':'.join(package.label() for package in self.current_packages)
        return self._apply_or_revert('apply', serializer, serialization_filename)

    def revert(self, serializer=None, serialization_filename=None):
        del self.current_session.environment[self.LOADED_PACKAGES_VARNAME]
        return self._apply_or_revert('revert', serializer, serialization_filename)

    def get_session_indices(self):
        indices = []
        #print(self.current_session_dir)
        for index_path in glob.glob(os.path.join(self.current_session_dir, "*.idx")):
            index_s = os.path.splitext(os.path.basename(index_path))[0]
            try:
                index = int(index_s)
                indices.append(Index(index, index_path))
            except:
                import traceback
                traceback.print_exc()
        indices.sort(key=lambda x: x.idx)
        return indices
            
    def get_package(self, package_label, package_list):
        l = package_label.split('/', 1)
        package_name = l[0]
        if len(l) > 1:
            package_version = l[1]
        else:
            package_version = None
        if package_version is not None:
            for op_symbol, operator in self.VERSION_OPERATORS:
                if package_version.startswith(op_symbol):
                    package_version = package_version[len(op_symbol):]
                    break
            else:
                operator = lambda x, v: x == v
        else:
            operator = lambda x, v: True
        packages = []
        for package in package_list:
            if package.name == package_name and operator(package.version, package_version):
                packages.append(package)
        if packages:
            packages.sort(key=lambda x: x.version)
            package = packages[-1]
        else:
            package = None
        return package
        
    def get_available_package(self, package_label):
        return self.get_package(package_label, Package.REGISTRY)

    def get_loaded_package(self, package_label):
        return self.get_package(package_label, self.current_packages)

    def _change(self, action, package_labels):
        packages = []
        if action == 'add':
            package_list = Package.REGISTRY
        else:
            package_list = self.current_packages
        for package_label in package_labels:
            package = self.get_package(package_label, package_list)
            if package is None:
                raise PackageNotFoundError("package {0} not found".format(package_label))
            if action == 'add' and package in self.current_packages:
                continue
            elif action == 'remove' and not package in self.current_packages:
                continue
            packages.append(package)
        indices = self.get_session_indices()
        if indices:
            index = max(i.idx for i in indices) + 1
        else:
            index = 1
        with open(os.path.join(self.current_session_dir, "{0}.idx".format(index)), 'w') as f_out:
            f_out.write('\n'.join("{0}:{1}".format(action, package.label()) for package in packages) + '\n')

    def add(self, package_labels):
        self._change('add', package_labels)

    def remove(self, package_labels):
        self._change('remove', package_labels)

