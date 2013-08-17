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
import collections
import configparser

from .environment import Environment
from .package import Package
from .errors import *
from .utils.debug import LOGGER
from .utils.trace import trace

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
        self._environment = Environment()
        self._orig_environment = self._environment.copy()
        self._packages = Packages()
        self.load(session_dir)

    @classmethod
    def get_session_config_file(cls, session_dir):
        return os.path.join(session_dir, cls.SESSION_CONFIG_FILE)

    def load(self, session_dir):
        self.unload_environment_packages()
        self.unload_packages()
        self.session_dir = os.path.abspath(session_dir)
        session_config_file = self.get_session_config_file(session_dir)
        self.session_name = None
        self.session_type = None
        packages_list = []
        if os.path.lexists(session_config_file):
            config = configparser.ConfigParser()
            config.read(session_config_file)
            session_section = config['session']
            self.session_name = session_section['name']
            self.session_type = session_section['type']
            packages_config = config['packages']
            #packages_dir_list_string = packages_config['directories']
            #if packages_dir_list_string:
            #    packages_dir_list = package_dir_list_string.split(':')
            #else:
            #    packages_dir_list = []
            packages_list_string = packages_config['loaded_packages']
            if packages_list_string:
                packages_list = package_list_string.split(':')
        else:
            LOGGER.warning("cannot load session config file {0}".format(session_config_file))
            return
        self.load_packages(packages_list)

    @classmethod
    def create_session_dir(cls, session_dir, session_name, session_type):
        if not os.path.isdir(session_dir):
            os.makedirs(session_dir)
        session_config_file = cls.get_session_config_file(session_dir)
        config = configparser.ConfigParser()
        config['session'] = {}
        config['session']['name'] = session_name
        config['session']['type'] = session_type
        config['packages'] = {}
        config['packages']['loaded_packages'] = ''
        config['packages']['directories'] = ''
        with open(session_config_file, "w") as f_config:
            config.write(f_config)
    
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
        return self.get_package(package_label, self._packages.values())

    def unload_environment_packages(self):
        loaded_package_labels_string = self._environment.get('UXS_LOADED_PACKAGES', None)
        if not loaded_package_labels_string:
            return
        loaded_package_labels = loaded_package_labels_string.split(':')
        for loaded_package_label in loaded_package_labels:
            loaded_package = self.get_available_package(loaded_package_label)
            if loaded_package is None:
                LOGGER.warning("inconsistent environment: cannot unload unknown package {0!r}".format(loaded_package_label))
                continue
            LOGGER.info("unloading package {0}...".format(loaded_package))
            loaded_package.revert(self)
        del self._environment['UXS_LOADED_PACKAGES']

    def unload_packages(self):
        for package_label, package in self._packages.items():
            #print("@@@ unload_packages::reverting {0}...".format(package_label))
            LOGGER.info("unloading package {0}...".format(package_label))
            package.revert(self)
        self._packages.clear()

    def load_packages(self, packages_list):
        for package_label in packages_list:
            package = self.get_available_package(package_label)
            package_label = package.label()
            #print("@@@ load_packages::applying {0}...".format(package_label))
            LOGGER.info("loading package {0}...".format(package_label))
            package.apply(self)
            self._packages[package_label] = package
                
    def store(self):
        packages_file = os.path.join(self.session_dir, self.PACKAGES_FILE)
        with open(packages_file, "w") as f_out:
            for package_label in self._packages:
                f_out.write(package_label + '\n')
        
    def add(self, package_labels):
        packages = []
        current_package_labels = []
        for package_label in package_labels:
            package = self.get_available_package(package_label)
            if package is None:
                LOGGER.error("package {0} not found".format(package_label))
                raise PackageNotFoundError("package {0} not found".format(package_label))
            package_label = package.label()
            if package_label in self._packages:
                LOGGER.info("package {0} already loaded".format(package_label))
                continue
            package = self.get_available_package(package_label)
            if package is None:
                raise AddPackageError("no such package: {0}".format(package_label))
            packages.append(package)
            current_package_labels.append(package_label)
        package_labels = current_package_labels
        for package_index, package in enumerate(packages):
            package_label = package.label()
            #print("@@@ add::applying {0}...".format(package_label))
            loaded_packages = list(self._packages.values()) + packages[package_index + 1:]
            unmatched_requirements = package.match_requirements(loaded_packages)
            if unmatched_requirements:
                for pkg, expression in unmatched_requirements:
                    LOGGER.error("{0}: unmatched requirement {1}".format(pkg, expression))
                if len(unmatched_requirements) > 1:
                    s = 's'
                else:    
                    s = ''
                raise AddPackageError("cannot add package {0}: {1} unmatched requirement{2}".format(package, len(unmatched_requirements), s))
            conflicts = package.match_conflicts(self._packages.values())
            if conflicts:
                for pkg0, expression, pkg1 in unmatched_requirements:
                    LOGGER.error("{0}: expression {1} conflicts with {2}".format(pkg0, expression, pkg1))
                if len(conflicts) > 1:
                    s = 's'
                else:    
                    s = ''
                raise AddPackageError("cannot add package {0}: {1} conflict{2}".format(package, len(unmatched_requirements), s))
            LOGGER.info("loading package {0}...".format(package_label))
            package.apply(self)
            self._packages[package_label] = package
        if self._packages.is_changed():
            self.store()
        
    def remove(self, package_labels):
        packages = []
        current_package_labels = []
        for package_label in package_labels:
            package = self.get_loaded_package(package_label)
            if package is None:
                LOGGER.error("package {0} not loaded".format(package_label))
                raise PackageNotFoundError("package {0} not loaded".format(package_label))
            package_label = package.label()
            if not package_label in self._packages:
                LOGGER.info("package {0} not loaded".format(package_label))
                continue
            package = self.get_available_package(package_label)
            if package is None:
                raise AddPackageError("no such package: {0}".format(package_label))
            packages.append(package)
            current_package_labels.append(package_label)
        package_labels = current_package_labels
        for package_index, package in enumerate(packages):
            package_label = package.label()
            loaded_packages = []
            for pkg_label, pkg in self._packages.items():
                if pkg_label != package_label:
                    loaded_packages.append(pkg)
            for pkg in loaded_packages:
                unmatched_requirements = pkg.match_requirements(filter(lambda pkg0: pkg0 is not pkg, loaded_packages))
                if unmatched_requirements:
                    for pkg, expression in unmatched_requirements:
                        LOGGER.error("after removal of {0}: {1}: unmatched requirement {2}".format(package, pkg, expression))
                    if len(unmatched_requirements) > 1:
                        s = 's'
                    else:    
                        s = ''
                    raise RemovePackageError("cannot remove package {0}: would leave {1} unmatched requirement{2}".format(package, len(unmatched_requirements), s))
            LOGGER.info("unloading package {0}...".format(package))
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
    
    def serialize(self, serializer):
        for var_name, var_value in self._environment.changeditems():
            orig_var_value = self._orig_environment.get(var_name, None)
            if var_value is None and orig_var_value is not None:
                # removed
                serializer.var_unset(var_name)
            elif var_value != orig_var_value:
                # set
                serializer.var_set(var_name, var_value)
        serializer.var_set("UXS_SESSION", self.session_dir)
        loaded_packages = ':'.join(self._packages.keys())
        serializer.var_set("UXS_LOADED_PACKAGES", loaded_packages)

    def serialize_stream(self, serializer, stream=None, serialization_filename=None):
        self.serialize(serializer)
        serializer.serialize(stream)
        if serialization_filename:
            serializer.serialize_remove_filename(stream, serialization_filename)
            serializer.serialize_remove_empty_directory(stream, os.path.dirname(serialization_filename))

    def serialize_file(self, serializer, serialization_filename):
        try:
            with open(serialization_filename, "w") as f_out:
                self.serialize_stream(serializer, stream=f_out, serialization_filename=serialization_filename)
        except Exception as e:
            trace()
            LOGGER.warning("cannot serialize {0}".format(serialization_filename))
