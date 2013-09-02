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
import itertools
import collections

from .environment import Environment
from .category import Category
from .package import Package
from .suite import Suite, ROOT
from .version_operators import get_version_operator
from .errors import *
from .session_config import SessionConfig
from .package_collection import PackageCollection
from .utils.debug import LOGGER, PRINT
from .utils.trace import trace
from .utils.table import Table
from .utils.sorted_dependencies import sorted_dependencies
from .utils.random_name import RandomNameSequence
from .utils.string import plural_string
from .utils import sequences


class Session(object):
    SESSION_SUFFIX = ".session"
    MODULE_PATTERN = "*.py"
    RANDOM_NAME_SEQUENCE = RandomNameSequence(width=5)
    SESSION_TYPE_TEMPORARY = 'temporary'
    SESSION_TYPE_PERSISTENT = 'persistent'
    SESSION_TYPES = [SESSION_TYPE_PERSISTENT, SESSION_TYPE_TEMPORARY]
    LOADED_PACKAGE_FORMAT_FULL =     "{__ordinal__}) {is_sticky} {category} {full_package} {tags}"
    LOADED_PACKAGE_FORMAT_SHORT =    "{__ordinal__}) {is_sticky} {category} {full_suite} {package} {tags}"
    AVAILABLE_PACKAGE_FORMAT_FULL =  "{__ordinal__}) {is_loaded}{is_conflicting} {category} {full_package} {tags}"
    AVAILABLE_PACKAGE_FORMAT_SHORT = "{__ordinal__}) {is_loaded}{is_conflicting} {category} {full_suite} {package} {tags}"
    PACKAGE_DIR_FORMAT = "{__ordinal__}) {package_dir}"
    PACKAGE_HEADER_DICT = {
        'category':         'CATEGORY',
        'is_sticky':        'S',
        'is_loaded':        'L',
        'is_conflicting':   'C',
        'package':          'PACKAGE',
        'full_package':     'PACKAGE',
        'suite':            'SUITE',
        'full_suite':       'SUITE',
        'tags':             'TAGS',
    }

    def __init__(self, session_root):
        self._environment = Environment()
        self._orig_environment = self._environment.copy()
        self._loaded_packages = PackageCollection()
        self._loaded_suites = PackageCollection()
        self._package_directories = []
        self._defined_packages = PackageCollection()
        self._available_packages = PackageCollection()
        self._orig_sticky_packages = set()
        self._sticky_packages = set()
        self._modules = {}
        self._show_full_label = False
        self._package_format = None
        self._available_package_format = None
        self._loaded_package_format = None
        self._version_defaults = {}
        self.load(session_root)

    def set_version_defaults(self, version_defaults):
        assert isinstance(version_defaults, collections.Mapping)
        self._version_defaults = version_defaults.copy()

    def set_show_full_label(self, value):
        self._show_full_label = value

    def get_show_full_label(self):
        return self._show_full_label

    show_full_label = property(get_show_full_label, set_show_full_label)

    def set_package_formats(self, *, available=None, loaded=None, generic=None):
        self._available_package_format = available
        self._loaded_package_format = loaded

    def set_package_formatting(self, package_format, show_full_label):
        self._package_format = package_format
        self._show_full_label = show_full_label

    def filter_packages(self, expression):
        for package_collection in self._defined_packages, self._available_packages:
            to_remove = set()
            for package_label, package in package_collection.items():
                expression.bind(package)
                if not expression.get_value():
                    to_remove.add(package_label)
            for package_label in to_remove:
                package = package_collection.pop(package_label)
                LOGGER.debug("discarding package {0} not matching expression {1}".format(package, expression))

    def _load_modules(self, package_dir):
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
        self.session_config = self.get_session_config(session_config_file)
        self.session_name = self.session_config['session']['name']
        self.session_type = self.session_config['session']['type']
        self.session_creation_time = self.session_config['session']['creation_time']
        package_directories_string = self.session_config['packages']['directories']
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
        # loaded packages
        packages_list_string = self.session_config['packages']['loaded_packages']
        if packages_list_string:
            packages_list = packages_list_string.split(':')
        else:
            packages_list = []
        self.load_packages(packages_list)
        # sticky packages
        packages_list_string = self.session_config['packages']['sticky_packages']
        if packages_list_string:
            packages_list = packages_list_string.split(':')
        else:
            packages_list = []
        self._sticky_packages.update(packages_list)
        self._orig_sticky_packages = self._sticky_packages.copy()

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
        if Package.SUITE_SEPARATOR in package_name:
            name_attr = 'full_name'
        else:
            name_attr = 'name'
        if len(l) > 1:
            package_version = l[1]
        else:
            package_version = None
        match_operator = get_version_operator(package_version)
        packages = []
        for package in package_list:
            if getattr(package, name_attr) == package_name and match_operator(package.version):
                packages.append(package)
        LOGGER.debug("get_package({0!r}) : packages={1}".format(package_label, [str(p) for p in packages]))
        if packages:
             package = self._choose_package(packages)
        else:
            package = None
        return package

    def _choose_package(self, packages):
        name_dict = {}
        full_name_dict = {}
        full_name_match_level = 0
        name_match_level = 1
        no_match_level = 2
        matches = []
        for package in packages:
            full_name = package.full_name
            if not full_name in full_name_dict:
                default_version = self._version_defaults.get(full_name, None)
                if default_version is None:
                    full_name_dict[full_name] = None
                else:
                    full_name_dict[full_name] = get_version_operator(default_version)
            full_name_operator = full_name_dict[full_name]
            #print("full name {0} operator: {1}".format(full_name, full_name_operator))
            if full_name_operator is not None and full_name_operator(package.version):
                LOGGER.debug("found full name matching version {0}".format(package))
                matches.append((full_name_match_level, package))
                continue
            name = package.name
            if not name in name_dict:
                default_version = self._version_defaults.get(name, None)
                if default_version is None:
                    name_dict[name] = None
                else:
                    name_dict[name] = get_version_operator(default_version)
            name_operator = name_dict[name]
            #print("name {0} operator: {1}".format(name, name_operator))
            if name_operator is not None and name_operator(package.version):
                LOGGER.debug("found name matching version {0}".format(package))
                matches.append((name_match_level, package))
                continue
            matches.append((no_match_level, package))
        keyfunc = lambda x: x[0]
        matches.sort(key=keyfunc)
        it = itertools.groupby(matches, keyfunc)
        level, level_matches = next(it)
        level_packages = sorted((package for l, package in level_matches), key=lambda package: package.version)
        return level_packages[-1]

        
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
                
    def store(self):
        self.session_config['packages']['loaded_packages'] = ':'.join(self._loaded_packages.keys())
        self.session_config['packages']['sticky_packages'] = ':'.join(self._sticky_packages)
        self.session_config.store()
        
    def add_directories(self, directories):
        changed = False
        for directory in directories:
            directory = os.path.normpath(os.path.abspath(directory))
            if directory in self._package_directories:
                LOGGER.warning("package directory {0} already in use".format(directory))
            else:
                LOGGER.info("adding package directory {0}...".format(directory))
                self._package_directories.append(directory)
                changed = True
        if changed:
            self.session_config['packages']['directories'] = ':'.join(self._package_directories)
            self.session_config.store()
        
    def remove_directories(self, directories):
        changed = False
        for directory in directories:
            directory = os.path.normpath(os.path.abspath(directory))
            if directory in self._package_directories:
                num_loaded_packages = 0
                for package in self._loaded_packages.values():
                    if package.package_dir == directory:
                        LOGGER.error("cannot remove directory {0}, since package {1} has been loaded from it".format(directory, package))
                        num_loaded_packages += 1
                if num_loaded_packages:
                    raise SessionError("cannot remove directory {0}: {1} loaded from it".format(
                        directory,
                        plural_string('package', num_loaded_packages)))
                if directory in self._package_directories:
                    LOGGER.info("removing package directory {0}...".format(directory))
                    self._package_directories.remove(directory)
                else:
                    LOGGER.warning("package directory {0} not in use".format(directory))
                changed = True
        if changed:
            self.session_config['packages']['directories'] = ':'.join(self._package_directories)
            self.session_config.store()
        
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
                package_label = package.full_label
#                if package_label in self._loaded_packages:
#                    LOGGER.info("package {0} already loaded".format(package_label))
#                    continue
                packages.append(package)
                yield packages
            if not packages:
                if missing_package_labels:
                    for package in missing_package_labels:
                        LOGGER.error("package {0} not found".format(package_label))
                    raise PackageNotFoundError("{0} not found".format(
                        plural_string('package', len(missing_package_labels))))
            package_labels = missing_package_labels

    def _get_subpackages(self, packages):
        all_packages = []
        while packages:
            new_packages = []
            for package in packages:
                if package in all_packages:
                    continue
                all_packages.append(package)
                if isinstance(package, Suite):
                    for subpackage in package.packages():
                        new_packages.append(subpackage)
            packages = new_packages
        return all_packages

    def _unloaded_packages(self, packages):
        unloaded_packages = []
        for package in packages:
            package_label = package.full_label
            if package_label in self._loaded_packages:
                LOGGER.info("package {0} already loaded".format(package_label))
                continue
            unloaded_packages.append(package)
        return unloaded_packages

    def add(self, package_labels, resolution_level=0, subpackages=False, sticky=False, dry_run=False):
        for packages in self.iteradd(package_labels):
            if subpackages:
                packages = self._get_subpackages(packages)
            required_packages = packages
            packages = self._unloaded_packages(packages)
            added_packages = self.add_packages(packages, resolution_level=resolution_level, dry_run=dry_run)
            if sticky:
                all_packages = set(required_packages).union(added_packages)
                self._sticky_packages.update(package.full_label for package in all_packages)
        
    def add_packages(self, packages, resolution_level=0, dry_run=False):
        package_dependencies = collections.defaultdict(set)
        available_packages = self.available_packages()
        defined_packages = self.defined_packages()
        packages_to_add = set()
        added_packages = []
        while packages:
            simulated_loaded_packages = list(sequences.unique(list(self._loaded_packages.values()) + packages))
            automatically_added_packages = []
            for package_index, package in enumerate(packages):
                package_label = package.full_label
                matched_requirements, unmatched_requirements = package.match_requirements(simulated_loaded_packages)
                if unmatched_requirements and resolution_level > 0:
                    # search in available_packages:
                    LOGGER.debug("resolution[1]: package {0}: searching {1} <{2}> in available packages...".format(
                        package,
                        plural_string('unmatched requirement', len(unmatched_requirements)),
                        ', '.join(str(e[-1]) for e in unmatched_requirements),
                    ))
                    matched_requirements, unmatched_requirements = package.match_requirements(available_packages)
                    for pkg0, expression, pkg1 in matched_requirements:
                        if not pkg1 in simulated_loaded_packages:
                            #LOGGER.debug("matching: {0}".format(pkg1))
                            if not pkg1 in automatically_added_packages:
                                LOGGER.info("package {0} will be automatically added".format(pkg1))
                                automatically_added_packages.append(pkg1)
                    if unmatched_requirements and resolution_level > 1:
                        # search in defined_packages:
                        LOGGER.debug("resolution[2]: package {0}: searching {1} <{2}> in defined packages...".format(
                            package,
                            plural_string('unmatched requirement', len(unmatched_requirements)),
                        ', '.join(str(e[-1]) for e in unmatched_requirements),
                        ))
                        matched_requirements, unmatched_requirements = package.match_requirements(defined_packages)
                        for pkg0, expression, pkg1 in matched_requirements:
                            if not pkg1 in simulated_loaded_packages:
                                #LOGGER.debug("matching: {0}".format(pkg1))
                                if not pkg1 in automatically_added_packages:
                                    LOGGER.info("package {0} will be automatically added".format(pkg1))
                                    automatically_added_packages.append(pkg1)
                if unmatched_requirements:
                    for pkg, expression in unmatched_requirements:
                        LOGGER.error("{0}: unmatched requirement {1}".format(pkg, expression))
                    raise AddPackageError("cannot add package {0}: {1}".format(
                        package,
                        plural_string('unmatched requirements', len(unmatched_requirements))))
                for pkg0, expression, pkg1 in matched_requirements:
                    package_dependencies[pkg0].add(pkg1)

                conflicts = package.match_conflicts(self._loaded_packages.values())
                if conflicts:
                    for pkg0, expression, pkg1 in conflicts:
                        LOGGER.error("{0}: expression {1} conflicts with {2}".format(pkg0, expression, pkg1))
                    raise AddPackageError("cannot add package {0}: {1}".format(
                        package,
                        plural_string('conflict', len(conflicts))))

                packages_to_add.update(packages)
                #packages = list(sequences.difference(packages, simulated_loaded_packages))
                LOGGER.debug("automatically_added_packages={0}".format([str(p) for p in automatically_added_packages]))
                packages = list(sequences.unique(automatically_added_packages))
        suites_to_add, packages_to_add = self._separate_suites(packages_to_add)
        for packages in suites_to_add, packages_to_add:
            sorted_packages = sorted_dependencies(package_dependencies, packages)
            self._add_packages(sorted_packages, dry_run=dry_run)
            added_packages.extend(packages)
        return added_packages

    def _separate_suites(self, packages):
        suites = []
        non_suites = []
        for package in packages:
            if isinstance(package, Suite):
                suites.append(package)
            else:
                non_suites.append(package)
        return suites, non_suites

    def _add_packages(self, packages, dry_run=False):
        if dry_run:
            header = '[dry-run] '
        else:
            header = ''
        for package in packages:
            LOGGER.info("{0}adding package {1}...".format(header, package))
            if dry_run:
                continue
            package.apply(self)
            self._loaded_packages[package.full_label] = package
            if isinstance(package, Suite):
                self._add_suite(package)

    def finalize(self):
        if self._loaded_packages.is_changed() or self._orig_sticky_packages != self._sticky_packages:
            self.store()
        
    def _add_suite(self, suite):
        self._loaded_suites.add_package(suite)
        for package in suite.packages():
            self._available_packages.add_package(package)

    def remove(self, package_labels, resolution_level=0, subpackages=False, sticky=False, dry_run=False):
        packages = []
        for package_label in package_labels:
            package = self.get_loaded_package(package_label)
            if package is None:
                LOGGER.error("package {0} not loaded".format(package_label))
                raise PackageNotFoundError("package {0} not loaded".format(package_label))
            package_label = package.full_label
            if package_label in self._loaded_packages:
                if not sticky:
                    LOGGER.info("package {0} is sticky, it will not be unloaded".format(package_label))
                    continue
            else:
                LOGGER.info("package {0} not loaded".format(package_label))
                continue
            package = self.get_available_package(package_label)
            if package is None:
                raise AddPackageError("no such package: {0}".format(package_label))
            packages.append(package)

        if subpackages:
            packages = self._get_subpackages(packages)

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
                            LOGGER.debug("resolution[1]: automatically removing {0} <{1}>...".format(
                                plural_string('depending package', len(unmatched_requirements)),
                                ', '.join(str(e[0]) for e in unmatched_requirements)
                            ))
                            for pkg0, expression in unmatched_requirements:
                                if not pkg in automatically_removed_packages:
                                    LOGGER.info("package {0} will be automatically removed".format(pkg))
                                    automatically_removed_packages.append(pkg)
                        else:
                            for pkg0, expression in unmatched_requirements:
                                LOGGER.error("after removal of {0}: {1}: unmatched requirement {2}".format(package, pkg, expression))
                            raise RemovePackageError("cannot remove package {0}: would leave {1}".format(
                                package,
                                plural_string('unmatched requirement', len(unmatched_requirements))))
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
            self._remove_packages(sorted_packages, dry_run=dry_run)

    def _remove_packages(self, packages, dry_run=False):
        if dry_run:
            header = '[dry-run] '
        else:
            header = ''
        for package in packages:
            LOGGER.info("{0}removing package {1}...".format(header, package))
            if dry_run:
                continue
            package.revert(self)
            del self._loaded_packages[package.full_label]
            if isinstance(package, Suite):
                self._remove_suite(package)
            self._sticky_packages.discard(package.full_label)
            
    def _remove_suite(self, suite):
        self._loaded_suites.remove_package(suite)
        for package in suite.packages():
            self._available_packages.remove_package(package)

    def clear(self, sticky=False, dry_run=False):
        packages_to_remove = reversed(list(self._loaded_packages.values()))
        if not sticky:
            lst = []
            for package in packages_to_remove:
                if package.full_label in self._sticky_packages:
                    LOGGER.info("sticky package {0} will not be removed".format(package))
                    continue
                lst.append(package)
            packages_to_remove = lst
        self._remove_packages(packages_to_remove, dry_run=dry_run)
            
    @property
    def environment(self):
        return self._environment

    @property
    def orig_environment(self):
        return self._orig_environment

    def __repr__(self):
        return "{c}(session_root={r!r}, session_name={n!r}, session_type={t!r})".format(c=self.__class__.__name__, r=self.session_root, n=self.session_name, t=self.session_type)
    __str__ = __repr__
    
    
    def is_sticky(self, package):
        return package.full_label in self._sticky_packages

    def is_loaded(self, package):
        return package.full_label in self._loaded_packages

    def is_conflicting(self, package):
        if package.match_conflicts(self._loaded_packages.values()):
            return True
        else:
            return False

    def _mark(self, b, symbol_True='*', symbol_False=''):
        if b:
            return symbol_True
        else:
            return symbol_False

    def _package_info(self, package):
        return {
            'category':         package.category,
            'is_sticky':        self._mark(self.is_sticky(package), 's', ' '),
            'is_loaded':        self._mark(self.is_loaded(package), 'l', ' '),
            'is_conflicting':   self._mark(self.is_conflicting(package), 'c', ' '),
            'package':          package.label,
            'full_package':     package.full_label,
            'suite':            package.suite.label,
            'full_suite':       package.suite.full_label,
            'tags':             ', '.join(str(tag) for tag in package.tags)
        }

    def get_available_package_format(self):
        if self._package_format:
            return self._package_format
        elif self._available_package_format:
            return self._available_package_format
        elif self._show_full_label:
            return self.AVAILABLE_PACKAGE_FORMAT_FULL
        else:
            return self.AVAILABLE_PACKAGE_FORMAT_SHORT

    def get_loaded_package_format(self):
        if self._package_format:
            return self._package_format
        elif self._loaded_package_format:
            return self._loaded_package_format
        elif self._show_full_label:
            return self.LOADED_PACKAGE_FORMAT_FULL
        else:
            return self.LOADED_PACKAGE_FORMAT_SHORT

    def show_packages(self, title, packages, package_format):
        d = {c: o for o, c in enumerate(Category.categories())}
        packages = list(packages)
        packages.sort(key=lambda package: d[package.category])
        packages.sort(key=lambda package: package.suite.full_label)

        t = Table(package_format, title=title)
        t.set_column_title(**self.PACKAGE_HEADER_DICT)
        for package in packages:
            t.add_row(**self._package_info(package))

        t.render(PRINT)

    @classmethod
    def make_package_format(cls, package_format_string):
        try:
            package_format_string.format(**cls.PACKAGE_HEADER_DICT)
        except Exception as e:
            raise ValueError("invalid package format {0!r}: {1}: {2}".format(package_format_string, e.__class__.__name__, e))
        else:
            return package_format_string

    def show_defined_packages(self):
        self.show_packages("Defined packages", self.defined_packages(), self.get_available_package_format())

    def show_available_packages(self):
        self.show_packages("Available packages", self.available_packages(), self.get_available_package_format())

    def show_loaded_packages(self):
        self.show_packages("Loaded packages", self.loaded_packages(), self.get_loaded_package_format())

    def show_package(self, package_label):
        package = self.get_available_package(package_label)
        if package is None:
            LOGGER.warning("package {0} not found".format(package_label))
        else:
            package.show()

    def show_package_directories(self):
        t = Table(self.PACKAGE_DIR_FORMAT, title="Package directories")
        for package_dir in self._package_directories:
            t.add_row(package_dir=package_dir)
        t.render(PRINT)

    def info(self):
        PRINT(Table.format_title("Session {0} at {1}".format(self.session_name, self.session_root)))
        PRINT("name          : {0}".format(self.session_name))
        PRINT("type          : {0}".format(self.session_type))
        PRINT("creation time : {0}".format(self.session_creation_time))
        self.show_package_directories()
        self.show_loaded_packages()

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
