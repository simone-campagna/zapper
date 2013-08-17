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
import collections

from .environment import Environment
from .package import Package, Category
from .errors import *
from .session_config import SessionConfig
from .utils.debug import LOGGER
from .utils.trace import trace
from .utils.show_sequence import show_sequence


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
    MODULE_PATTERN = "uxs_*.py"
    VERSION_OPERATORS = (
        ('==',          lambda x, v: x == v),
        ('!=',          lambda x, v: x != v),
        ('<',           lambda x, v: x <  v),
        ('<=',          lambda x, v: x <= v),
        ('>',           lambda x, v: x >  v),
        ('>=',          lambda x, v: x >= v),
    )

    def __init__(self, manager, session_dir):
        self._environment = Environment()
        self._orig_environment = self._environment.copy()
        self._loaded_packages = Packages()
        self._package_directories = []
        self._available_packages = Packages()
        self.load(session_dir)

    def _load_modules(self, module_dir):
        #print("+++", module_dir)
        modules = []
        for module_path in glob.glob(os.path.join(module_dir, self.MODULE_PATTERN)):
            Package.set_module_dir(module_dir)
            try:
                modules.append(self._load_module(module_path))
            finally:
                Package.unset_module_dir()
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
        self._available_packages.clear()
        for package_dir in self._package_directories:
            self._load_modules(package_dir)
            for package in Package.__registry__[package_dir]:
                self._available_packages[package.label()] = package

    @classmethod
    def get_session_config_file(cls, session_dir):
        return os.path.join(session_dir, cls.SESSION_CONFIG_FILE)

    @classmethod
    def get_session_config(cls, session_config_file):
        return SessionConfig(session_config_file)

    @classmethod
    def write_session_config(cls, session_config, session_config_file):
        with open(session_config_file, "w") as f_out:
            session_config.write(f_out)

    def load(self, session_dir):
        self.session_dir = os.path.abspath(session_dir)
        session_config_file = self.get_session_config_file(session_dir)
        if not os.path.lexists(session_config_file):
            LOGGER.warning("cannot load session config file {0}".format(session_config_file))
        session_config = self.get_session_config(session_config_file)
        self.session_name = session_config['session']['name']
        self.session_type = session_config['session']['type']
        package_directories_string = session_config['packages']['directories']
        if package_directories_string:
            package_directories = package_directories_string.split(':')
        else:
            package_directories = []
        uxs_package_dir = os.environ.get("UXS_PACKAGE_DIR", None)
        if uxs_package_dir:
            package_directories.extend(uxs_package_dir.split(':'))
        self._package_directories = package_directories
        self.load_available_packages()
        packages_list_string = session_config['packages']['loaded_packages']
        if packages_list_string:
            packages_list = packages_list_string.split(':')
        else:
            packages_list = []
        self.load_packages(packages_list)

    @classmethod
    def create_session_dir(cls, manager, session_dir, session_name, session_type):
        if not os.path.isdir(session_dir):
            os.makedirs(session_dir)
        session_config_file = cls.get_session_config_file(session_dir)
        session_config = cls.get_session_config(session_config_file)
        session_config['session']['name'] = session_name
        session_config['session']['type'] = session_type
        package_directories = []
        if manager.user_package_dir and os.path.lexists(manager.user_package_dir):
            package_directories.append(manager.user_package_dir)
        if manager.uxs_package_dir and os.path.lexists(manager.uxs_package_dir):
            package_directories.append(manager.uxs_package_dir)
        package_directories = [os.path.normpath(os.path.abspath(d)) for d in package_directories]
        session_config['packages']['directories'] = ':'.join(package_directories)
        #session_config.write(sys.stdout)
        session_config.store()
    
    @classmethod
    def create(cls, manager, session_dir, session_name, session_type):
        cls.create_session_dir(manager, session_dir, session_name, session_type)
        return cls(session_dir)
        
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
        return self.get_package(package_label, self._available_packages.values())

    def get_loaded_package(self, package_label):
        return self.get_package(package_label, self._loaded_packages.values())

    def loaded_packages(self):
        return self._loaded_packages.values()

    def available_packages(self):
        return self._available_packages.values()

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
        for package_label, package in self._loaded_packages.items():
            #print("@@@ unload_packages::reverting {0}...".format(package_label))
            LOGGER.info("unloading package {0}...".format(package_label))
            package.revert(self)
        self._loaded_packages.clear()

    def load_packages(self, packages_list):
        self.unload_environment_packages()
        self.unload_packages()
        for package_label in packages_list:
            package = self.get_available_package(package_label)
            package_label = package.label()
            #print("@@@ load_packages::applying {0}...".format(package_label))
            LOGGER.info("loading package {0}...".format(package_label))
            package.apply(self)
            self._loaded_packages[package_label] = package
                
    def store(self):
        session_config_file = self.get_session_config_file(self.session_dir)
        session_config = self.get_session_config(session_config_file)
        session_config['packages']['loaded_packages'] = ':'.join(self._loaded_packages.keys())
        session_config.store()
        
    def add_directories(self, directories):
        changed = False
        for directory in directories:
            directory = os.path.normpath(os.path.abspath(directory))
            if not directory in self._package_directories:
                self._package_directories.append(directory)
                changed = True
        if changed:
            session_config_file = self.get_session_config_file(self.session_dir)
            session_config = self.get_session_config(session_config_file)
            session_config['packages']['directories'] = ':'.join(self._package_directories)
            session_config.store()
        
    def remove_directories(self, directories):
        changed = False
        for directory in directories:
            directory = os.path.normpath(os.path.abspath(directory))
            if directory in self._package_directories:
                self._package_directories.remove(directory)
                changed = True
        if changed:
            session_config_file = self.get_session_config_file(self.session_dir)
            session_config = self.get_session_config(session_config_file)
            session_config['packages']['directories'] = ':'.join(self._package_directories)
            session_config.store()
        
    def add(self, package_labels):
        packages = []
        current_package_labels = []
        for package_label in package_labels:
            package = self.get_available_package(package_label)
            if package is None:
                LOGGER.error("package {0} not found".format(package_label))
                raise PackageNotFoundError("package {0} not found".format(package_label))
            package_label = package.label()
            if package_label in self._loaded_packages:
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
            loaded_packages = list(self._loaded_packages.values()) + packages[package_index + 1:]
            unmatched_requirements = package.match_requirements(loaded_packages)
            if unmatched_requirements:
                for pkg, expression in unmatched_requirements:
                    LOGGER.error("{0}: unmatched requirement {1}".format(pkg, expression))
                if len(unmatched_requirements) > 1:
                    s = 's'
                else:    
                    s = ''
                raise AddPackageError("cannot add package {0}: {1} unmatched requirement{2}".format(package, len(unmatched_requirements), s))
            conflicts = package.match_conflicts(self._loaded_packages.values())
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
            self._loaded_packages[package_label] = package
        if self._loaded_packages.is_changed():
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
            if not package_label in self._loaded_packages:
                LOGGER.info("package {0} not loaded".format(package_label))
                continue
            package = self.get_available_package(package_label)
            if package is None:
                raise AddPackageError("no such package: {0}".format(package_label))
            packages.append(package)
            current_package_labels.append(package_label)
        package_labels = current_package_labels
        new_loaded_packages = []
        for package_label, package in self._loaded_packages.items():
            if not package_label in package_labels:
                new_loaded_packages.append(package)
        #print("loaded:", [package.label() for package in self.loaded_packages()])
        #print("to remove:", [package.label() for package in packages])
        #print("new loaded:", [package.label() for package in new_loaded_packages])
        for pkg in new_loaded_packages:
            unmatched_requirements = pkg.match_requirements(filter(lambda pkg0: pkg0 is not pkg, new_loaded_packages))
            if unmatched_requirements:
                for pkg, expression in unmatched_requirements:
                    LOGGER.error("after removal of {0}: {1}: unmatched requirement {2}".format(package, pkg, expression))
                if len(unmatched_requirements) > 1:
                    s = 's'
                else:    
                    s = ''
                raise RemovePackageError("cannot remove package {0}: would leave {1} unmatched requirement{2}".format(package, len(unmatched_requirements), s))

        for package in packages:
            package
            LOGGER.info("unloading package {0}...".format(package))
            package.revert(self)
            del self._loaded_packages[package.label()]
            
        if self._loaded_packages.is_changed():
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
    
    
    def show_packages(self, title, packages):
        if Category.__categories__:
            max_category_len = max(len(category) for category in Category.__categories__)
        else:
            max_category_len = 0
        print("=== {0}:".format(title))
        fmt = "{{0:{np}d}} {{1:{lc}s}} {{2}}".format(np=len(str(len(packages) - 1)), lc=max_category_len)
        for package_index, package in enumerate(packages):
            print(fmt.format(package_index, package.category, package.label()))

    def show_available_packages(self):
        self.show_packages("Available packages", self.available_packages())

    def show_loaded_packages(self):
        self.show_packages("Loaded packages", self.loaded_packages())

    def show_package(self, package_label):
        package = self.get_available_package(package_label)
        if package is None:
            print("package {0} not found".format(package_label))
        else:
            package.show()

    def show_package_directories(self):
        show_sequence("Package directories", self._package_directories)

    def info(self):
        print("=== Session name: {0}".format(self.session_name))
        print("            dir:  {0}".format(self.session_dir))
        print("            type: {0}".format(self.session_type))
        show_sequence("Package directories", self._package_directories)
        self.show_packages("Loaded packages", self.loaded_packages())

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
        loaded_packages = ':'.join(self._loaded_packages.keys())
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
