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
#import shutil
import collections

from .environment import Environment
from .category import Category
from .package import Package
from .suite import Suite, ROOT
from .errors import *
from .session_config import SessionConfig
from .utils.debug import LOGGER, PRINT
from .utils.trace import trace
from .utils.show_table import show_table, show_title
from .utils.sorted_dependencies import sorted_dependencies
from .utils.random_name import RandomNameSequence
from .utils import sequences


class Packages(collections.OrderedDict):
    def __init__(self):
        super().__init__(self)
        self._changed_package_full_labels = []

    def is_changed(self):
        return bool(self._changed_package_full_labels)

    def __setitem__(self, package_full_label, package):
        old_package = super().get(package_full_label, None)
        if old_package != package:
            self._changed_package_full_labels.append(package_full_label)
        super().__setitem__(package_full_label, package)
       
    def __delitem__(self, package_full_label):
        if package_full_label in self:
            self._changed_package_full_labels.append(package_full_label)
            super().__delitem__(package_full_label)

    def add_package(self, package):
        package_full_label = package.full_label()
        if package_full_label in self and self[package_full_label] is not package:
            #raise SessionError("package {0} hides {1}".format(package.full_label(), self[package_full_label].full_label()))
            LOGGER.warning("package {0} hides {1}".format(package.full_label(), self[package_full_label].full_label()))
        self[package_full_label] = package

    def remove_package(self, package):
        package_full_label = package.full_label()
        del self[package_full_label]

class Session(object):
    SESSION_SUFFIX = ".session"
    MODULE_PATTERN = "uxs_*.py"
    VERSION_OPERATORS = (
        ('==',          lambda x, v: x == v),
        ('!=',          lambda x, v: x != v),
        ('<',           lambda x, v: x <  v),
        ('<=',          lambda x, v: x <= v),
        ('>',           lambda x, v: x >  v),
        ('>=',          lambda x, v: x >= v),
    )
    RANDOM_NAME_SEQUENCE = RandomNameSequence(width=5)
    SESSION_TYPE_TEMPORARY = 'temporary'
    SESSION_TYPE_PERSISTENT = 'persistent'
    SESSION_TYPES = [SESSION_TYPE_PERSISTENT, SESSION_TYPE_TEMPORARY]

    def __init__(self, manager, session_root):
        self._environment = Environment()
        self._orig_environment = self._environment.copy()
        self._loaded_packages = Packages()
        self._loaded_suites = Packages()
        self._package_directories = []
        self._defined_packages = Packages()
        self._available_packages = Packages()
        self._modules = {}
        self.load(session_root)

    def _load_modules(self, package_dir):
        #print("+++", package_dir)
        modules = []
        for module_path in glob.glob(os.path.join(package_dir, self.MODULE_PATTERN)):
            module_path = os.path.normpath(os.path.abspath(module_path))
            if not module_path in self._modules:
                Package.set_package_dir(package_dir)
                try:
                    module = self._load_module(module_path)
                finally:
                    Package.unset_package_dir()
                self._modules[module_path] = module
                modules.append(module)
            else:
                modules.append(self._modules[module_path])
        return modules

    def _load_module(self, module_path):
        package_dirname, module_basename = os.path.split(module_path)
        module_name = module_basename[:-3]
        sys_path = [package_dirname]
        module_info = imp.find_module(module_name, sys_path)
        if module_info:
            module = imp.load_module(module_name, *module_info)
        return module

    def set_defined_packages(self):
        self._defined_packages.clear()
        for package_dir in self._package_directories:
            self._load_modules(package_dir)
            for package in Package.registered_entry('package_dir', package_dir):
                self._defined_packages.add_package(package)

    def set_available_packages(self):
        self._available_packages.clear()
        for suite in self._loaded_suites.values():
            for package in suite.packages():
                self._available_packages.add_package(package)

    @classmethod
    def get_session_config_file(cls, session_root):
        return session_root + cls.SESSION_SUFFIX

    @classmethod
    def get_session_root(cls, session_config_file):
        l = len(cls.SESSION_SUFFIX)
        session_root, session_suffix = \
            session_config_file[:-l], session_config_file[-l:]
        if session_suffix != cls.SESSION_SUFFIX:
            raise SessionError("invalid session config file name {0}".format(session_config_file))
        return session_root

    @classmethod
    def get_session_config(cls, session_config_file):
        return SessionConfig(session_config_file)

    @classmethod
    def write_session_config(cls, session_config, session_config_file):
        with open(session_config_file, "w") as f_out:
            session_config.write(f_out)

    @classmethod
    def copy(cls, source_session_root, target_session_root):
        source_session_config_file = cls.get_session_config_file(source_session_root)
        source_session_config = cls.get_session_config(source_session_config_file)
        source_session_config['session']['name'] = os.path.basename(target_session_root)
        source_session_config['session']['type'] = cls.SESSION_TYPE_PERSISTENT
        source_session_config['session']['creation_time'] = SessionConfig.current_time()
        target_session_config_file = cls.get_session_config_file(target_session_root)
        cls.write_session_config(source_session_config, target_session_config_file)

    def load(self, session_root):
        self.session_root = os.path.abspath(session_root)
        session_config_file = self.get_session_config_file(session_root)
        if not os.path.lexists(session_config_file):
            LOGGER.warning("cannot load session config file {0}".format(session_config_file))
        session_config = self.get_session_config(session_config_file)
        self.session_name = session_config['session']['name']
        self.session_type = session_config['session']['type']
        self.session_creation_time = session_config['session']['creation_time']
        package_directories_string = session_config['packages']['directories']
        if package_directories_string:
            package_directories = package_directories_string.split(':')
        else:
            package_directories = []
        uxs_package_dir = os.environ.get("UXS_PACKAGE_DIR", None)
        if uxs_package_dir:
            package_directories.extend(uxs_package_dir.split(':'))
        self._package_directories = package_directories
        self.set_defined_packages()
        self.set_available_packages()
        packages_list_string = session_config['packages']['loaded_packages']
        if packages_list_string:
            packages_list = packages_list_string.split(':')
        else:
            packages_list = []
        self.load_packages(packages_list)

    @classmethod
    def create_unique_session_root(cls, sessions_dir):
        for name in cls.RANDOM_NAME_SEQUENCE:
            session_name = "uxs{0}".format(name)
            session_root = os.path.join(sessions_dir, session_name)
            session_config_file = cls.get_session_config_file(session_root)
            if os.path.lexists(session_config_file):
                # name already in use
                LOGGER.warning("name {0} already in use - discarded".format(session_name))
                continue
            try:
                os.open(session_config_file, os.O_CREAT | os.O_EXCL)
            except OSError as e:
                # file already exists
                LOGGER.warning("file {0} already exists - {1} discarded".format(session_config_file, session_name))
                continue
            return session_root
            
    @classmethod
    def create_session_config(cls, manager, session_root, session_name, session_type):
        session_config_file = cls.get_session_config_file(session_root)
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
        session_config.store()
    
    @classmethod
    def delete_session_root(cls, session_root, session_name=None):
        if session_name is None:
            session_name = os.path.basename(session_root)
        LOGGER.info("deleting session {0}...".format(session_name))
        session_config_file = cls.get_session_config_file(session_root)
        if not os.path.lexists(session_config_file):
            LOGGER.error("cannot delete session {0}: it does not exists".format(session_name))
        os.remove(session_config_file)

    @classmethod
    def get_session_roots(cls, sessions_dir, session_name_pattern='*'):
        session_roots = []
        for session_config_file in glob.glob(os.path.join(sessions_dir, session_name_pattern + cls.SESSION_SUFFIX)):
            session_root = session_config_file[:-len(cls.SESSION_SUFFIX)]
            session_roots.append(session_root)
        return session_roots

    @classmethod
    def create(cls, manager, session_root, session_name, session_type):
        cls.create_session_config(manager, session_root, session_name, session_type)
        return cls(session_root)
        
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
        LOGGER.debug("get_package({0!r}) : packages={1}".format(package_label, [str(p) for p in packages]))
        if packages:
            packages.sort(key=lambda x: x.version)
            LOGGER.debug("get_package({0!r}) : sorted_packages={1}".format(package_label, [str(p) for p in packages]))
            package = packages[-1]
        else:
            package = None
        return package

#    def get_defined_package(self, package_label):
#        WRONG: labels are not unique in defined packages
#        return self.get_package(package_label, self._defined_packages.values())

    def get_available_package(self, package_label):
        return self.get_package(package_label, self._available_packages.values())

    def get_loaded_package(self, package_label):
        return self.get_package(package_label, self._loaded_packages.values())

    def loaded_packages(self):
        return self._loaded_packages.values()

    def defined_packages(self):
        return self._defined_packages.values()

    def available_packages(self):
        return self._available_packages.values()

    def unload_environment_packages(self):
        loaded_package_labels_string = self._environment.get('UXS_LOADED_PACKAGES', None)
        if not loaded_package_labels_string:
            return
        loaded_package_labels = loaded_package_labels_string.split(':')

        # loading necessary suites
        for packages in self.iteradd(loaded_package_labels):
            for package in packages:
                if isinstance(package, Suite):
                    self._add_suite(package)

        for loaded_package_label in loaded_package_labels:
            loaded_package = self.get_available_package(loaded_package_label)
            if loaded_package is None:
                LOGGER.warning("inconsistent environment: cannot unload unknown package {0!r}".format(loaded_package_label))
                continue
            LOGGER.info("removing package {0}...".format(loaded_package))
            loaded_package.revert(self)
        del self._environment['UXS_LOADED_PACKAGES']

    def unload_packages(self):
        for package_label, package in self._loaded_packages.items():
            LOGGER.info("removing package {0}...".format(package_label))
            package.revert(self)
        self._loaded_packages.clear()

    def load_packages(self, packages_list):
        self._add_suite(ROOT)
        self.unload_environment_packages()
        self.unload_packages()
        self.add(packages_list)
#        for package_label in packages_list:
#            package = self.get_available_package(package_label)
#            package_label = package.label()
#            LOGGER.info("adding package {0}...".format(package_label))
#            package.apply(self)
#            self._loaded_packages[package_label] = package
                
    def store(self):
        session_config_file = self.get_session_config_file(self.session_root)
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
            session_config_file = self.get_session_config_file(self.session_root)
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
            session_config_file = self.get_session_config_file(self.session_root)
            session_config = self.get_session_config(session_config_file)
            session_config['packages']['directories'] = ':'.join(self._package_directories)
            session_config.store()
        
    def iteradd(self, package_labels):
        while package_labels:
            packages = []
            missing_package_labels = []
            for package_label in package_labels:
                package = self.get_available_package(package_label)
                if package is None:
                    missing_package_labels.append(package_label)
                    continue
                    #LOGGER.error("package {0} not found".format(package_label))
                    #raise PackageNotFoundError("package {0} not found".format(package_label))
                package_label = package.label()
                if package_label in self._loaded_packages:
                    LOGGER.info("package {0} already loaded".format(package_label))
                    continue
                packages.append(package)
                yield packages
            if not packages:
                if missing_package_labels:
                    for package in missing_package_labels:
                        LOGGER.error("package {0} not found".format(package_label))
                    if len(missing_package_labels) > 1:
                        s = 's' 
                    else:        
                        s = ''
                    raise PackageNotFoundError("#{0} package{1} not found".format(len(missing_package_labels), s))
            package_labels = missing_package_labels

    def add(self, package_labels, resolution_level=0):
        for packages in self.iteradd(package_labels):
            self.add_packages(packages, resolution_level=resolution_level)
        
    def add_packages(self, packages, resolution_level=0):
        package_dependencies = collections.defaultdict(set)
        available_packages = self.available_packages()
        packages_to_add = set()
        while packages:
            simulated_loaded_packages = list(sequences.unique(list(self._loaded_packages.values()) + packages))
            automatically_added_packages = []
            for package_index, package in enumerate(packages):
                package_label = package.label()
                matched_requirements, unmatched_requirements = package.match_requirements(simulated_loaded_packages)
                if unmatched_requirements and resolution_level > 0:
                    matched_requirements, unmatched_requirements = package.match_requirements(available_packages)
                    for pkg0, expression, pkg1 in matched_requirements:
                        if not pkg1 in simulated_loaded_packages:
                            #LOGGER.debug("matching: {0}".format(pkg1))
                            if not pkg1 in automatically_added_packages:
                                LOGGER.info("package {0} will be automatically added".format(pkg1))
                                automatically_added_packages.append(pkg1)
                if unmatched_requirements:
                    for pkg, expression in unmatched_requirements:
                        LOGGER.error("{0}: unmatched requirement {1}".format(pkg, expression))
                    if len(unmatched_requirements) > 1:
                        s = 's'
                    else:    
                        s = ''
                    raise AddPackageError("cannot add package {0}: #{1} unmatched requirement{2}".format(package, len(unmatched_requirements), s))
                for pkg0, expression, pkg1 in matched_requirements:
                    package_dependencies[pkg0].add(pkg1)

                conflicts = package.match_conflicts(self._loaded_packages.values())
                if conflicts:
                    for pkg0, expression, pkg1 in conflicts:
                        LOGGER.error("{0}: expression {1} conflicts with {2}".format(pkg0, expression, pkg1))
                    if len(conflicts) > 1:
                        s = 's'
                    else:    
                        s = ''
                    raise AddPackageError("cannot add package {0}: #{1} conflict{2}".format(package, len(conflicts), s))

                packages_to_add.update(packages)
                #packages = list(sequences.difference(packages, simulated_loaded_packages))
                LOGGER.debug("automatically_added_packages={0}".format([str(p) for p in automatically_added_packages]))
                packages = list(sequences.unique(automatically_added_packages))
        suites_to_add, packages_to_add = self._separate_suites(packages_to_add)
        for packages in suites_to_add, packages_to_add:
            sorted_packages = sorted_dependencies(package_dependencies, packages)
            self._add_packages(sorted_packages)

    def _separate_suites(self, packages):
        suites = []
        non_suites = []
        for package in packages:
            if isinstance(package, Suite):
                suites.append(package)
            else:
                non_suites.append(package)
        return suites, non_suites

    def _add_packages(self, packages):
        for package in packages:
            LOGGER.info("adding package {0}...".format(package))
            package.apply(self)
            self._loaded_packages[package.label()] = package
            if isinstance(package, Suite):
                self._add_suite(package)
        if self._loaded_packages.is_changed():
            self.store()
        
    def _add_suite(self, suite):
        self._loaded_suites.add_package(suite)
        for package in suite.packages():
            self._available_packages.add_package(package)

    def remove(self, package_labels, resolution_level=0):
        packages = []
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

        packages_to_remove = set()

        while packages:
            automatically_removed_packages = []
            # check missing dependencies:
            for package in packages:
                new_loaded_packages = [pkg for pkg in self._loaded_packages.values() if not pkg in packages]
                for pkg in new_loaded_packages:
                    matched_requirements, unmatched_requirements = pkg.match_requirements(filter(lambda pkg0: pkg0 is not pkg, new_loaded_packages))
                    if unmatched_requirements:
                        if resolution_level > 0:
                            for pkg0, expression in unmatched_requirements:
                                if not pkg in automatically_removed_packages:
                                    LOGGER.info("package {0} will be automatically removed".format(pkg))
                                    automatically_removed_packages.append(pkg)
                        else:
                            for pkg0, expression in unmatched_requirements:
                                LOGGER.error("after removal of {0}: {1}: unmatched requirement {2}".format(package, pkg, expression))
                            if len(unmatched_requirements) > 1:
                                s = 's'
                            else:    
                                s = ''
                            raise RemovePackageError("cannot remove package {0}: would leave #{1} unmatched requirement{2}".format(package, len(unmatched_requirements), s))
            packages_to_remove.update(packages)
            packages = list(sequences.unique(automatically_removed_packages))

        # compute dependencies between packages to remove:
        # it is used to remove packages in the correct order
        package_dependencies = collections.defaultdict(set)
        for package in packages_to_remove:
            matched_requirements, unmatched_requirements = package.match_requirements(filter(lambda pkg0: pkg0 is not package, packages_to_remove))
            for pkg0, expression, pkg1 in matched_requirements:
                package_dependencies[pkg0].add(pkg1)

        suites_to_remove, packages_to_remove = self._separate_suites(packages_to_remove)
        for packages in packages_to_remove, suites_to_remove:
            sorted_packages = sorted_dependencies(package_dependencies, packages)
            self._remove_packages(sorted_packages)

    def _remove_packages(self, packages):
        for package in packages:
            LOGGER.info("removing package {0}...".format(package))
            package.revert(self)
            del self._loaded_packages[package.label()]
            if isinstance(package, Suite):
                self._remove_suite(package)
            
        if self._loaded_packages.is_changed():
            self.store()

    def _remove_suite(self, suite):
        self._loaded_suites.remove_package(suite)
        for package in suite.packages():
            self._available_packages.remove_package(package)

    def clear(self):
        self._remove_packages(reversed(list(self._loaded_packages.values())))
            
    @property
    def environment(self):
        return self._environment

    @property
    def orig_environment(self):
        return self._orig_environment

    def __repr__(self):
        return "{c}(session_root={r!r}, session_name={n!r}, session_type={t!r})".format(c=self.__class__.__name__, r=self.session_root, n=self.session_name, t=self.session_type)
    __str__ = __repr__
    
    
    def show_packages(self, title, packages):
        d = {c: o for o, c in enumerate(Category.categories())}
        packages = sorted(packages, key=lambda package: d[package.category])
        show_table(title,
            [(package.category,
              package._suite.full_label(),
              package.label(),
              ', '.join(str(tag) for tag in package.tags)) for package in packages],
            header=('CATEGORY', 'SUITE', 'PACKAGE', 'TAGS'),
        )

    def show_defined_packages(self):
        self.show_packages("Defined packages", self.defined_packages())

    def show_available_packages(self):
        self.show_packages("Available packages", self.available_packages())

    def show_loaded_packages(self):
        self.show_packages("Loaded packages", self.loaded_packages())

    def show_package(self, package_label):
        package = self.get_available_package(package_label)
        if package is None:
            LOGGER.warning("package {0} not found".format(package_label))
        else:
            package.show()

    def show_package_directories(self):
        show_table("Package directories", self._package_directories)

    def info(self):
        show_title("Session {0} at {1}".format(self.session_name, self.session_root))
        PRINT("name          : {0}".format(self.session_name))
        PRINT("type          : {0}".format(self.session_type))
        PRINT("creation time : {0}".format(self.session_creation_time))
        show_table("Package directories", self._package_directories)
        self.show_packages("Loaded packages", self.loaded_packages())

    def translate(self, translator):
        for var_name, var_value in self._environment.changeditems():
            orig_var_value = self._orig_environment.get(var_name, None)
            if var_value is None and orig_var_value is not None:
                # removed
                translator.var_unset(var_name)
            elif var_value != orig_var_value:
                # set
                translator.var_set(var_name, var_value)
        translator.var_set("UXS_SESSION", self.session_root)
        loaded_packages = ':'.join(self._loaded_packages.keys())
        translator.var_set("UXS_LOADED_PACKAGES", loaded_packages)

    def translate_stream(self, translator, stream=None, translation_filename=None):
        self.translate(translator)
        translator.translate(stream)
        if translation_filename:
            translator.translate_remove_filename(stream, translation_filename)

    def translate_file(self, translator, translation_filename):
        try:
            with open(translation_filename, "w") as f_out:
                self.translate_stream(translator, stream=f_out, translation_filename=translation_filename)
        except Exception as e:
            trace()
            LOGGER.warning("cannot translate {0}".format(translation_filename))
