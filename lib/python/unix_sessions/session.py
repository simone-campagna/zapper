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

import collections
import os

from .environment import Environment
from .package import Package

class Packages(collections.OrderedDict):
    def __init__(self):
        super().__init__(self)
        self._changed_package_labels = []

    def is_changed(self):
        return bool(self._changed_package_labels)

    def __setitem__(self, package_label, package):
        old_package = super().get(package_label, None)
        if old_package != package:
            self._changed_package_labels.append(package_label)
        super().__setitem__(package_label, package)
       
    def __delitem__(self, package_label):
        if package_label in self:
            self._changed_package_labels.append(package_label)
        super().__delitem__(package_label)

class Session(object):
    SESSION_CONFIG_FILE = "session.config"
    PACKAGES_FILE = "packages.txt"
    VERSION_OPERATORS = (
        ('==',          lambda x, v: x == v),
        ('!=',          lambda x, v: x != v),
        ('<',           lambda x, v: x <  v),
        ('<=',          lambda x, v: x <= v),
        ('>',           lambda x, v: x >  v),
        ('>=',          lambda x, v: x >= v),
    )

    def __init__(self, session_dir):
        self.session_dir = os.path.abspath(session_dir)
        session_config_file = os.path.join(self.session_dir, self.SESSION_CONFIG_FILE)
        with open(session_config_file, "r") as f_in:
            line = f_in.readline().strip()
            self.session_type, self.session_name = line.split(":", 1)
        self._environment = Environment()
        self._orig_environment = self._environment.copy()
        self._packages = Packages()
        self.load()

    @classmethod
    def create_session_dir(cls, session_dir, session_name, session_type):
        if not os.path.isdir(session_dir):
            os.makedirs(session_dir)
        session_config_file = os.path.join(session_dir, cls.SESSION_CONFIG_FILE)
        with open(session_config_file, "w") as f_out:
            f_out.write("{0}:{1}\n".format(session_type, session_name))
    
    @classmethod
    def create(cls, session_dir, session_name, session_type):
        cls.create_session_dir(session_dir, session_name, session_type)
        return cls(session_dir)
        
    def packages(self):
        return self._packages.values()
        
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
        return self.get_package(package_label, self._packages.keys())

    def unload(self):
        for package_label, package in self._packages.items():
            package.revert(self)
        self._packages.clear()

    def load(self):
        self.unload()
        packages_file = os.path.join(self.session_dir, self.PACKAGES_FILE)
        if os.path.lexists(packages_file):
            with open(packages_file, "r") as f_in:
                for line in f_in:
                    package_label = line.strip()
                    package = self.get_available_package(package_label)
                    package.apply(self)
                    self._packages[package_label] = package
                
    def store(self):
        packages_file = os.path.join(self.session_dir, self.PACKAGES_FILE)
        with open(packages_file, "w") as f_out:
            for package_label in self._packages:
                f_out.write(package_label + '\n')
        
    def add(self, package_labels):
        for package_label in package_labels:
            if not package_label in self._packages:
                package = self.get_available_package(package_label)
                package.apply(self)
                self._packages[package_label] = package
        if self._packages.is_changed():
            self.store()
        
    def remove(self, package_labels):
        for package_label in package_labels:
            if not package_label in self._packages:
                package = self.get_loaded_package(package_label)
                package.revert(self)
                del self._packages[package_label]
        if self._packages.is_changed():
            self.store()

    @property
    def environment(self):
        return self._environment

    @property
    def orig_environment(self):
        return self._orig_environment

    def __repr__(self):
        return "{c}(session_dir={d!r}, session_name={n!r}, session_type={t!r})".format(c=self.__class__.__name__, d=self.session_dir, n=self.session_name, t=self.session_type)
    __str__ = __repr__
    
    def serialize_stream(self, serializer, stream=None, serialization_filename=None):
        for var_name, var_value in self._environment.changeditems():
            orig_var_value = self._orig_environment.get(var_name, None)
            if var_value is None and orig_var_value is not None:
                # removed
                serializer.var_unset(var_name)
            elif var_value != orig_var_value:
                # set
                serializer.var_set(var_name, var_value)
        serializer.serialize(stream)
        if serialization_filename:
            serializer.serialize_remove_filename(stream, serialization_filename)

    def serialize(self, serializer, serialization_filename):
        with open(serialization_filename, "w") as f_out:
            self.serialize_stream(serializer, stream=f_out, serialization_filename=serialization_filename)
