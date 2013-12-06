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
from .parameters import PARAMETERS
from .package import Package
from .product import Product
from .suite import Suite, ROOT
from .version_operators import get_version_operator
from .errors import *
from .session_config import SessionConfig
from .package_collection import PackageCollection
from .utils.debug import LOGGER, PRINT
from .utils.trace import trace
from .utils.table import Table, validate_format
from .utils.sorted_dependencies import sorted_dependencies
from .utils.random_name import RandomNameSequence
from .utils.strings import plural_string, string_to_bool, bool_to_string, string_to_list, list_to_string
from .utils.sort_keys import SortKeys
from .utils import sequences


class Session(object):
    SESSION_SUFFIX = ".session"
    MODULE_PATTERN = "*.py"
    TEMPORARY_SESSION_NAME_FORMAT = 'zap{name}'
    RANDOM_NAME_SEQUENCE = RandomNameSequence(width=8 - len(TEMPORARY_SESSION_NAME_FORMAT.format(name='')))
    SESSION_TYPE_TEMPORARY = 'temporary'
    SESSION_TYPE_PERSISTENT = 'persistent'
    SESSION_TYPES = [SESSION_TYPE_PERSISTENT, SESSION_TYPE_TEMPORARY]
    LOADED_PACKAGE_FORMAT =     "{__ordinal__:>3d}) {abbr_type}{is_sticky} {category} {abs_package} {tags}"
    AVAILABLE_PACKAGE_FORMAT =  "{__ordinal__:>3d}) {abbr_type}{is_loaded}{is_conflicting} {category} {abs_package} {tags}"
    PACKAGE_HEADER_DICT = collections.OrderedDict((
        ('__ordinal__',      '#'),
        ('category',         'CATEGORY'),
        ('abbr_type',        'T'),
        ('is_sticky',        'S'),
        ('is_loaded',        'L'),
        ('is_conflicting',   'C'),
        ('type',             'TYPE'),
        ('version',          'VERSION'),
        ('product',          'PRODUCT'),
        ('package',          'PACKAGE'),
        ('abs_package',      'PACKAGE'),
        ('suite',            'SUITE'),
        ('abs_suite',        'SUITE'),
        ('tags',             'TAGS'),
        ('package_dir',      'PACKAGE_DIR'),
        ('package_file',     'PACKAGE_FILE'),
        ('package_module',   'PACKAGE_MODULE'),
    ))
    PACKAGE_DIR_FORMAT = "{__ordinal__:>3d}) {package_dir}"
    PACKAGE_DIR_HEADER_DICT = collections.OrderedDict((
        ('__ordinal__',      '#'),
        ('package_dir',      'DIRECTORY'),
    ))
    DEFAULT_PACKAGE_SORT_KEYS = SortKeys("category:product:version", PACKAGE_HEADER_DICT, 'package')
    DEFAULT_PACKAGE_DIR_SORT_KEYS = SortKeys("", PACKAGE_DIR_HEADER_DICT, 'package directory')
    def __init__(self, session_root, *, load=True):
        self._environment = Environment()
        self._orig_environment = self._environment.copy()
        self._loaded_packages = PackageCollection()
        self._loaded_suites = PackageCollection()
        self._package_directories = []
        self._defined_packages = PackageCollection()
        self._available_packages = PackageCollection()
        self._enable_default_version = False
        self._show_header = True
        self._show_header_if_empty = True
        self._orig_sticky_packages = set()
        self._sticky_packages = set()
        self._modules = {}
        self._dry_run = False
        self._force = False
        self._package_format = None
        self._available_package_format = None
        self._loaded_package_format = None
        self._package_dir_format = None
        self.set_package_sort_keys(None)
        self.set_package_dir_sort_keys(None)
        self._version_defaults = {}
        if load:
            self.load(session_root)
        self._deleted = False # if True, session will be deleted in finalize()

    def sync(self):
        pass

    def delete(self):
        if self.is_read_only():
            LOGGER.error("cannot delete read-only session {!r}".format(self.session_name))
        else:
            self.clear(sticky=True)
            self._deleted = True

    def set_dry_run(self, dry_run):
        self._dry_run = bool(dry_run)

    def set_force(self, force):
        self._force = bool(force)

    def new_session(self, session_root):
        session = Session(session_root, load=False)
        session.load(session_root, load_packages=True, loaded_package_directories=self._package_directories)
        #self._environment.var_set("ZAPPER_SESSION", self.session_root)
        return session

    def is_read_only(self):
        return self.session_read_only and not self._force

    def check_read_only(self):
        if self.session_read_only:
            if self._force:
                if not getattr(self, '__changing_read_only_message', None):
                    LOGGER.warning("you are changing read-only session {!r}".format(self.session_name))
                    setattr(self, '__changing_read_only_message', True)
            else:
                raise SessionError("cannot change read-only session {}".format(self.session_name))

    def set_enable_default_version(self, enable_default_version):
        self._enable_default_version = enable_default_version

    def set_show_header(self, show_header, show_header_if_empty):
        self._show_header = show_header
        self._show_header_if_empty = show_header_if_empty

    def set_version_defaults(self, version_defaults):
        assert isinstance(version_defaults, collections.Mapping), "version_defaults is not a Mapping: {}".format(version_defaults)
        self._version_defaults = version_defaults.copy()

    def set_package_formats(self, *, available=None, loaded=None, generic=None):
        self._available_package_format = available
        self._loaded_package_format = loaded

    def set_package_formatting(self, package_format):
        self._package_format = package_format

    def set_package_dir_format(self, package_dir_format):
        self._package_dir_format = package_dir_format

    def filter_packages(self, expression):
        for package_collection in self._defined_packages, self._available_packages:
            to_unload = set()
            for package_label, package in package_collection.items():
                expression.bind(package)
                if not expression.get_value():
                    to_unload.add(package_label)
            for package_label in to_unload:
                package = package_collection.pop(package_label)
                LOGGER.debug("discarding package {0} not matching expression {1}".format(package, expression))

    @classmethod
    def _normpath(cls, path):
        return os.path.normpath(os.path.abspath(os.path.expanduser(os.path.expandvars(path))))

    def _load_modules(self, package_dir):
        modules = []
        LOGGER.info("loading modules from {}".format(package_dir))
        for module_path in glob.glob(os.path.join(package_dir, self.MODULE_PATTERN)):
            module_path = self._normpath(module_path)
            if not module_path in self._modules:
                PARAMETERS.set_current_dir(package_dir)
                try:
                    module = self._load_module(module_path)
                except Exception as e:
                    trace(True)
                    LOGGER.warning("cannot impot package file {!r}: {}: {}".format(module_path, e.__class__.__name__, e))
                    continue
                finally:
                    PARAMETERS.unset_current_dir()
                self._modules[module_path] = module
                modules.append(module)
            else:
                modules.append(self._modules[module_path])
        return modules

    def _load_module(self, module_path):
        package_dirname, module_basename = os.path.split(module_path)
        module_name = module_basename[:-3]
        sys_path = [package_dirname]
        LOGGER.info("loading module {}".format(module_path))
        module_info = imp.find_module(module_name, sys_path)
        if module_info:
            PARAMETERS.set_current_module_file(module_name, module_path)
            try:
                module = imp.load_module(module_name, *module_info)
            finally:
                PARAMETERS.unset_current_module_file()
        return module

    def get_package_directories(self):
        return tuple(self._package_directories)

    def set_defined_packages(self, *, loaded_package_directories):
        self._defined_packages.clear()
        for package_dir in self._package_directories:
            if loaded_package_directories and package_dir in loaded_package_directories:
                continue
            self._load_modules(package_dir)
            for package in Package.registered_entry('package_dir', package_dir):
                self._defined_packages.add_package(package)

    def set_available_packages(self):
        self._available_packages.clear()
        for suite in self._loaded_suites.values():
            if not suite.source_dir in self._package_directories:
                continue
            for package in suite.packages():
                if not package.source_dir in self._package_directories:
                    continue
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

    def load(self, session_root, *, load_packages=True, loaded_package_directories=None):
        self.session_root = os.path.abspath(session_root)
        session_config_file = self.get_session_config_file(self.session_root)
        if not os.path.lexists(session_config_file):
            LOGGER.warning("cannot load session config file {0}".format(session_config_file))
        self.session_config = self.get_session_config(session_config_file)
        self.session_name = self.session_config['session']['name']
        self.session_type = self.session_config['session']['type']
        self.session_description = self.session_config['config']['description']
        self.session_read_only = False
        current_session_read_only_string = self.session_config['config']['read_only']
        if current_session_read_only_string:
            current_session_read_only = string_to_bool(current_session_read_only_string)
        else:
            current_session_read_only = False
        
        self.session_creation_time = self.session_config['session']['creation_time']
        package_directories_string = self.session_config['config']['directories']
        if package_directories_string:
            package_directories = package_directories_string.split(':')
        else:
            package_directories = []
        zapper_package_dir = os.environ.get("ZAPPER_PACKAGE_DIR", None)
        if zapper_package_dir:
            package_directories.extend(zapper_package_dir.split(':'))
        self._package_directories = package_directories
        self.set_defined_packages(loaded_package_directories=loaded_package_directories)
        self.set_available_packages()
        if load_packages:
            # loaded packages
            packages_list = string_to_list(self.session_config['packages']['loaded_packages'])
            #packages_list_string = self.session_config['packages']['loaded_packages']
            #if packages_list_string:
            #    packages_list = packages_list_string.split(':')
            #else:
            #    packages_list = []
            self.initialize_loaded_packages(packages_list)
        # sticky packages
        packages_list = string_to_list(self.session_config['packages']['sticky_packages'])
        #packages_list_string = self.session_config['packages']['sticky_packages']
        #if packages_list_string:
        #    packages_list = packages_list_string.split(':')
        #else:
        #    packages_list = []
        self._sticky_packages.update(packages_list)
        self._orig_sticky_packages = self._sticky_packages.copy()
        # this must be at the end!
        self.session_read_only = current_session_read_only

    @classmethod
    def create_unique_session_root(cls, sessions_dir):
        for name in cls.RANDOM_NAME_SEQUENCE:
            session_name = cls.TEMPORARY_SESSION_NAME_FORMAT.format(name=name)
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
                LOGGER.warning("cannot create config file {}: {}: {}".format(session_config_file, e.__class__.__name__, e))
                LOGGER.warning("file {} already exists - {} discarded".format(session_config_file, session_name))
                continue
            return session_root
            
    @classmethod
    def create_session_config(cls, manager, session_root, session_name, session_type, session_description, session_packages=None):
        session_config_file = cls.get_session_config_file(session_root)
        session_config = cls.get_session_config(session_config_file)
        session_config['session']['name'] = session_name
        session_config['session']['type'] = session_type
        session_config['config']['description'] = session_description
        package_directories = string_to_list(manager.get_user_config_key('directories'))
        package_directories = [cls._normpath(d) for d in package_directories]
        session_config['config']['directories'] = list_to_string(package_directories)
        if session_packages:
            session_config['packages']['loaded_packages'] = list_to_string(session_packages)
        session_config.store()
    
    @classmethod
    def delete_session_root(cls, session_root, session_name=None, *, force=False):
        if session_name is None:
            session_name = os.path.basename(session_root)
        LOGGER.info("deleting session {!r}...".format(session_name))
        session_config_file = cls.get_session_config_file(session_root)
        if not os.path.lexists(session_config_file):
            LOGGER.error("cannot delete session {!r}: it does not exists".format(session_name))
        session_config = cls.get_session_config(session_config_file)
        session_read_only = string_to_bool(session_config['config']['read_only'])
        if session_read_only:
            if force:
                LOGGER.warning("you are deleting read-only session {!r}".format(session_name))
            else:
                LOGGER.error("cannot delete read-only session {!r}".format(session_name))
                return
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
        
    def get_packages(self, package_label, package_list):
        labels = package_label.split(Package.SUITE_SEPARATOR)
        packages = []
        sub_label = labels.pop(0)
        sub_packages = self._get_packages_from_label(sub_label, package_list)
        #print("label={!r}, sub_label={!r}, labels={}, sub_packages={}".format(package_label, sub_label, labels, sub_packages))
        for sub_package in sub_packages:
            if labels:
                if isinstance(sub_package, Suite):
                    packages.extend(self._get_suite_packages(sub_package, labels))
            else:
                packages.append(sub_package)
        return packages

    def _get_suite_packages(self, suite, labels):
        assert isinstance(suite, Suite), suite
        #print("@@@", repr(suite), '|'.join(str(p) for p in suite.packages()), labels)
        package_label = labels.pop(0)
        sub_packages = self._get_packages_from_label(package_label, suite.packages())
        #print("--> package_label={!r} labels={}, sub_packages={}".format(package_label, labels, '|'.join(str(p) for p in sub_packages)))
        result = []
        if labels: 
            for sub_package in sub_packages:
                if isinstance(sub_package, Suite):
                    result = self._get_suite_packages(sub_package, list(labels))
        else:
            result.extend(sub_packages)
        #print("package_label={!r}, result={}".format(package_label, '|'.join(str(p) for p in result)))
        return result

    def _get_packages_from_label(self, package_label, package_list):
        if package_label == ROOT.label:
            return [ROOT]
        l = package_label.split(Package.VERSION_SEPARATOR, 1)
        package_name = l[0]
        if len(l) > 1:
            package_version = l[1]
        else:
            if not self._enable_default_version:
                LOGGER.warning("invalid package name {} (default version is not allowed)".format(package_label))
                raise PackageNotFoundError("package {0} not found".format(package_label))
            package_version = None

        #print("### package_label={!r} package_name={!r} package_version={!r}".format(package_label, package_name, package_version))
        match_operator = get_version_operator(package_version)
        packages = []
        for package in package_list:
            if package.name == package_name and match_operator(package.version):
                packages.append(package)
        LOGGER.debug("get_package({!r}) : packages={}".format(package_label, [str(p) for p in packages]))
        return packages

    def get_package(self, package_label, package_list):
        packages = self.get_packages(package_label, package_list)
        if packages:
             package = self._choose_package(packages)
        else:
            package = None
        return package

    def _choose_package(self, packages):
        name_dict = {}
        absolute_name_dict = {}
        absolute_name_match_level = 0
        name_match_level = 1
        no_match_level = 2
        matches = []
        for package in packages:
            absolute_name = package.absolute_name
            if not absolute_name in absolute_name_dict:
                default_version = self._version_defaults.get(absolute_name, None)
                if default_version is None:
                    absolute_name_dict[absolute_name] = None
                else:
                    absolute_name_dict[absolute_name] = get_version_operator(default_version)
            absolute_name_operator = absolute_name_dict[absolute_name]
            #print("absolute name {0} operator: {1}".format(absolute_name, absolute_name_operator))
            if absolute_name_operator is not None and absolute_name_operator(package.version):
                LOGGER.debug("found absolute name matching version {0}".format(package))
                matches.append((absolute_name_match_level, package))
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

    def unload_environment_packages(self, *, ignore_errors=True):
        """unload_environment_packages() -> list of previously loaded packages
Remove all the previously loaded packages (from environment variable
$ZAPPER_LOADED_PACKAGES) and returns the list of unloaded packages""" 
        env_loaded_packages = []
        loaded_package_labels_string = self._environment.get('ZAPPER_LOADED_PACKAGES', None)
        if not loaded_package_labels_string:
            return env_loaded_packages
        loaded_package_labels = loaded_package_labels_string.split(':')

        # loading necessary suites
        for packages in self.iterdep(loaded_package_labels, ignore_errors=ignore_errors):
            for package in packages:
                if isinstance(package, Suite):
                    self._add_suite(package)

        for loaded_package_label in loaded_package_labels:
            loaded_package = self.get_available_package(loaded_package_label)
            if loaded_package is None:
                LOGGER.warning("inconsistent environment: cannot unload unknown package {0!r}".format(loaded_package_label))
                continue
            #LOGGER.info("unloading package {0}...".format(loaded_package))
            loaded_package.unload(self, info=False)
            env_loaded_packages.append(loaded_package)
        del self._environment['ZAPPER_LOADED_PACKAGES']
        return env_loaded_packages

    def unload_all_loaded_packages(self):
        for package_label, package in self._loaded_packages.items():
            LOGGER.info("unloading package {0}...".format(package_label))
            package.unload(self)
        self._loaded_packages.clear()

    def initialize_loaded_packages(self, packages_list):
        self._add_suite(ROOT)
        env_loaded_packages = set(self.unload_environment_packages(ignore_errors=True))
        self.unload_all_loaded_packages()
        self.load_package_labels(packages_list, ignore_errors=True, info=False)
        loaded_packages = set(self.loaded_packages())
        for package in loaded_packages.difference(env_loaded_packages):
            LOGGER.info("package {} has been loaded".format(package))
        for package in env_loaded_packages.difference(loaded_packages):
            LOGGER.info("package {} has been unloaded".format(package))
        
                
    def store(self):
        self.check_read_only()
        sticky_packages = self._sticky_packages.intersection(self._loaded_packages.keys())
        self.session_config['packages']['loaded_packages'] = ':'.join(self._loaded_packages.keys())
        self.session_config['packages']['sticky_packages'] = ':'.join(sticky_packages)
        if not self._dry_run:
            self.session_config.store()
        
    def iterdep(self, package_labels, *, ignore_errors=False):
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
                package_label = package.absolute_label
#                if package_label in self._loaded_packages:
#                    LOGGER.info("package {0} already loaded".format(package_label))
#                    continue
                packages.append(package)
            yield packages
            if not packages:
                if missing_package_labels:
                    for package in missing_package_labels:
                        LOGGER.error("package {0} not found".format(package_label))
                    if ignore_errors:
                        del missing_package_labels[:]
                    else:
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
            package_label = package.absolute_label
            if package_label in self._loaded_packages:
                LOGGER.info("package {0} already loaded".format(package_label))
                continue
            unloaded_packages.append(package)
        return unloaded_packages

    def load_package_labels(self, package_labels, *, resolution_level=0, subpackages=False, sticky=False, simulate=False, ignore_errors=False, info=True):
        self.check_read_only()
        for packages in self.iterdep(package_labels, ignore_errors=ignore_errors):
            if subpackages:
                packages = self._get_subpackages(packages)
            required_packages = packages
            packages = self._unloaded_packages(packages)
            loaded_packages = self.load_packages(packages, resolution_level=resolution_level, simulate=simulate, info=info)
            if sticky:
                all_packages = set(required_packages).union(loaded_packages)
                self._sticky_packages.update(package.absolute_label for package in all_packages)
        
    def load_packages(self, packages, resolution_level=0, simulate=False, info=True):
        package_dependencies = collections.defaultdict(set)
        available_packages = self.available_packages()
        defined_packages = self.defined_packages()
        packages_to_load = set()
        loaded_packages = []
        while packages:
            simulated_loaded_packages = list(sequences.unique(list(self._loaded_packages.values()) + packages))
            automatically_loaded_packages = []
            for package_index, package in enumerate(packages):
                package_label = package.absolute_label
                matched_requirements, unmatched_requirements = package.match_requirements(simulated_loaded_packages)
                if unmatched_requirements and resolution_level > 0:
                    # search in available_packages:
                    LOGGER.debug("resolution[1]: package {0}: searching {1} <{2}> in available packages...".format(
                        package,
                        plural_string('unmatched requirement', len(unmatched_requirements)),
                        ', '.join(str(e[-1]) for e in unmatched_requirements),
                    ))
                    matched_requirements, unmatched_requirements = package.match_requirements(available_packages)
                    for pkg0, expression, pkg_lst in matched_requirements:
                        pkg1 = pkg_lst[-1]
                        if not pkg1 in simulated_loaded_packages:
                            #LOGGER.debug("matching: {0}".format(pkg1))
                            if not pkg1 in automatically_loaded_packages:
                                LOGGER.info("package {0} will be automatically loaded".format(pkg1))
                                automatically_loaded_packages.append(pkg1)
                    if unmatched_requirements and resolution_level > 1:
                        # search in defined_packages:
                        LOGGER.debug("resolution[2]: package {0}: searching {1} <{2}> in defined packages...".format(
                            package,
                            plural_string('unmatched requirement', len(unmatched_requirements)),
                        ', '.join(str(e[-1]) for e in unmatched_requirements),
                        ))
                        matched_requirements, unmatched_requirements = package.match_requirements(defined_packages)
                        for pkg0, expression, pkg_lst in matched_requirements:
                            pkg1 = pkg_lst[-1]
                            if not pkg1 in simulated_loaded_packages:
                                #LOGGER.debug("matching: {0}".format(pkg1))
                                if not pkg1 in automatically_loaded_packages:
                                    LOGGER.info("package {0} will be automatically loaded".format(pkg1))
                                    automatically_loaded_packages.append(pkg1)
                if unmatched_requirements:
                    for pkg, expression in unmatched_requirements:
                        LOGGER.error("{0}: unmatched requirement {1}".format(pkg, expression))
                    raise LoadPackageError("cannot load package {0}: {1}".format(
                        package,
                        plural_string('unmatched requirements', len(unmatched_requirements))))
                for pkg0, expression, pkg_lst in matched_requirements:
                    package_dependencies[pkg0].add(pkg_lst[-1])

                conflicts = package.match_conflicts(simulated_loaded_packages)
                if conflicts:
                    for pkg0, expression, pkg1 in conflicts:
                        LOGGER.error("{0}: expression {1} conflicts with {2}".format(pkg0, expression, pkg1))
                    raise LoadPackageError("cannot load package {0}: {1}".format(
                        package,
                        plural_string('conflict', len(conflicts))))

                packages_to_load.update(packages)
                #packages = list(sequences.difference(packages, simulated_loaded_packages))
                LOGGER.debug("automatically_loaded_packages={0}".format([str(p) for p in automatically_loaded_packages]))
                packages = list(sequences.unique(automatically_loaded_packages))
        suites_to_load, packages_to_load = self._separate_suites(packages_to_load)
        for packages in suites_to_load, packages_to_load:
            sorted_packages = sorted_dependencies(package_dependencies, packages)
            self._load_packages(sorted_packages, simulate=simulate, info=info)
            loaded_packages.extend(packages)
        return loaded_packages

    def _separate_suites(self, packages):
        suites = []
        non_suites = []
        for package in packages:
            if isinstance(package, Suite):
                suites.append(package)
            else:
                non_suites.append(package)
        return suites, non_suites

    def _load_packages(self, packages, simulate=False, info=True):
        if simulate:
            header = '[dry-run] '
        else:
            header = ''
        for package in packages:
            if info:
                LOGGER.info("{0}loading package {1}...".format(header, package))
            if simulate:
                continue
            package.load(self, info=info)
            self._loaded_packages[package.absolute_label] = package
            if isinstance(package, Suite):
                self._add_suite(package)

    def finalize(self):
        if not self.is_read_only():
            if self._loaded_packages.is_changed() or self._orig_sticky_packages != self._sticky_packages:
                if not self._dry_run:
                    self.store()
        if self._deleted:
            self.delete_session_root(self.session_root, self.session_name, force=self._force)
        
    def _add_suite(self, suite):
        self._loaded_suites.add_package(suite)
        for package in suite.packages():
            if not package.source_dir in self._package_directories:
                continue
            self._available_packages.add_package(package)

    def unload_package_labels(self, package_labels, resolution_level=0, subpackages=False, sticky=False, simulate=False):
        self.check_read_only()
        packages = []
        for package_label in package_labels:
            package = self.get_loaded_package(package_label)
            if package is None:
                LOGGER.error("package {0} not loaded".format(package_label))
                raise PackageNotFoundError("package {0} not loaded".format(package_label))
            package_label = package.absolute_label
            if package_label in self._loaded_packages:
                if sticky:
                    LOGGER.info("package {0} is sticky, it will not be unloaded".format(package_label))
                    continue
            else:
                LOGGER.info("package {0} not loaded".format(package_label))
                continue
            package = self.get_available_package(package_label)
            if package is None:
                raise LoadPackageError("no such package: {0}".format(package_label))
            packages.append(package)

        if subpackages:
            packages = self._get_subpackages(packages)

        packages_to_unload = set()

        while packages:
            automatically_unloaded_packages = []
            # check missing dependencies:
            for package in packages:
                new_loaded_packages = [pkg for pkg in self._loaded_packages.values() if not pkg in packages]
                for pkg in new_loaded_packages:
                    matched_requirements, unmatched_requirements = pkg.match_requirements(filter(lambda pkg0: pkg0 is not pkg, new_loaded_packages))
                    if unmatched_requirements:
                        if resolution_level > 0:
                            LOGGER.debug("resolution[1]: automatically unloading {0} <{1}>...".format(
                                plural_string('depending package', len(unmatched_requirements)),
                                ', '.join(str(e[0]) for e in unmatched_requirements)
                            ))
                            for pkg0, expression in unmatched_requirements:
                                if not pkg in automatically_unloaded_packages:
                                    LOGGER.info("package {0} will be automatically unloaded".format(pkg))
                                    automatically_unloaded_packages.append(pkg)
                        else:
                            for pkg0, expression in unmatched_requirements:
                                LOGGER.error("after unload of {0}: {1}: unmatched requirement {2}".format(package, pkg0, expression))
                            raise UnloadPackageError("cannot unload package {0}: would leave {1}".format(
                                package,
                                plural_string('unmatched requirement', len(unmatched_requirements))))
            packages_to_unload.update(packages)
            packages = list(sequences.unique(automatically_unloaded_packages))

        # compute dependencies between packages to unload:
        # it is used to unload packages in the correct order
        package_dependencies = collections.defaultdict(set)
        for package in packages_to_unload:
            matched_requirements, unmatched_requirements = package.match_requirements(filter(lambda pkg0: pkg0 is not package, packages_to_unload))
            for pkg0, expression, pkg_lst in matched_requirements:
                package_dependencies[pkg0].add(pkg_lst[-1])

        suites_to_unload, packages_to_unload = self._separate_suites(packages_to_unload)
        for packages in packages_to_unload, suites_to_unload:
            sorted_packages = sorted_dependencies(package_dependencies, packages)
            self._unload_packages(sorted_packages, simulate=simulate)

    def _unload_packages(self, packages, simulate=False):
        if simulate:
            header = '[dry-run] '
        else:
            header = ''
        for package in packages:
            LOGGER.info("{0}unloading package {1}...".format(header, package))
            if simulate:
                continue
            package.unload(self)
            del self._loaded_packages[package.absolute_label]
            if isinstance(package, Suite):
                self._remove_suite(package)
            self._sticky_packages.discard(package.absolute_label)
            
    def _remove_suite(self, suite):
        self._loaded_suites.remove_package(suite)
        for package in suite.packages():
            self._available_packages.remove_package(package)

    def clear(self, sticky=False, simulate=False):
        self.check_read_only()
        packages_to_unload = reversed(list(self._loaded_packages.values()))
        if not sticky:
            lst = []
            for package in packages_to_unload:
                if package.absolute_label in self._sticky_packages:
                    LOGGER.info("sticky package {0} will not be unloaded".format(package))
                    continue
                lst.append(package)
            packages_to_unload = lst
        self._unload_packages(packages_to_unload, simulate=simulate)
            
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
        return package.absolute_label in self._sticky_packages

    def is_loaded(self, package):
        return package.absolute_label in self._loaded_packages

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
        package_type = package.package_type()
        return {
            'category':         package.category,
            'type':             package_type,
            'abbr_type':        package_type[0],
            'is_sticky':        self._mark(self.is_sticky(package), 's', ' '),
            'is_loaded':        self._mark(self.is_loaded(package), 'l', ' '),
            'is_conflicting':   self._mark(self.is_conflicting(package), 'c', ' '),
            'product':          package.name,
            'version':          package.version,
            'package':          package.label,
            'abs_package':      package.absolute_label,
            'suite':            package.suite.label,
            'abs_suite':        package.suite.absolute_label,
            'tags':             ', '.join(str(tag) for tag in package.tags),
            'package_dir':      package.source_dir,
            'package_file':     package.source_file,
            'package_module':   package.source_module,
        }

    def get_available_package_format(self):
        if self._package_format:
            return self._package_format
        elif self._available_package_format:
            return self._available_package_format
        else:
            return self.AVAILABLE_PACKAGE_FORMAT

    def get_loaded_package_format(self):
        if self._package_format:
            return self._package_format
        elif self._loaded_package_format:
            return self._loaded_package_format
        else:
            return self.LOADED_PACKAGE_FORMAT

    def set_package_sort_keys(self, sort_keys):
        if sort_keys is None:
            sort_keys = self.DEFAULT_PACKAGE_SORT_KEYS
        self._package_sort_keys = sort_keys

    def set_package_dir_sort_keys(self, sort_keys):
        if sort_keys is None:
            sort_keys = self.DEFAULT_PACKAGE_DIR_SORT_KEYS
        self._package_dir_sort_keys = sort_keys

    @classmethod
    def PackageFormat(cls, package_format):
        if package_format is not None:
            validate_format(package_format, **cls.PACKAGE_HEADER_DICT)
        return package_format

    @classmethod
    def PackageDirFormat(cls, package_dir_format):
        if package_dir_format is not None:
            validate_format(package_dir_format, **cls.PACKAGE_DIR_HEADER_DICT)
        return package_dir_format

    @classmethod
    def PackageSortKeys(cls, package_sort_keys):
        return SortKeys(package_sort_keys, cls.PACKAGE_HEADER_DICT, 'package')

    @classmethod
    def PackageDirSortKeys(cls, package_dir_sort_keys):
        return SortKeys(package_dir_sort_keys, cls.PACKAGE_DIR_HEADER_DICT, 'package directory')

    def show_packages(self, title, packages, package_format, *, sort_keys=None, show_title=False):
        if sort_keys is None:
            sort_keys = self._package_sort_keys

        package_infos = [self._package_info(package) for package in packages]

        sort_keys.sort(package_infos)

        if not show_title:
            title = None

        t = Table(package_format, show_header=self._show_header, show_header_if_empty=self._show_header_if_empty, title=title)
        t.set_column_title(**self.PACKAGE_HEADER_DICT)
        for package_info in package_infos:
            t.add_row(**package_info)

        t.render(PRINT)

    def show_defined_packages(self, *, show_title=False):
        self.show_packages("Defined packages", self.defined_packages(), self.get_available_package_format(), show_title=show_title)

    def show_available_packages(self, package_labels, *, show_title=False):
        if package_labels:
            packages = []
            for package_label in package_labels:
                for package in self.get_packages(package_label, self.available_packages()):
                    if not package in packages:
                        packages.append(package)
        else:
            packages = self.available_packages()
        self.show_packages("Available packages", packages, self.get_available_package_format(), show_title=show_title)

    def show_loaded_packages(self, *, show_title=False):
        self.show_packages("Loaded packages", self.loaded_packages(), self.get_loaded_package_format(), show_title=show_title)

    def show_package(self, package_label):
        package = self.get_available_package(package_label)
        if package is None:
            LOGGER.warning("package {0} not found".format(package_label))
        else:
            package.show()

    def show_package_directories(self, *, sort_keys=None, show_title=False):
        if sort_keys is None:
            sort_keys = self._package_dir_sort_keys

        package_dir_format = self._package_dir_format
        if not package_dir_format:
            package_dir_format = self.PACKAGE_DIR_FORMAT

        rows = []
        for package_dir in self._package_directories:
            rows.append(dict(package_dir=package_dir))
       
        sort_keys.sort(rows)

        if show_title:
            title = "Package directories"
        else:
            title = None
        t = Table(package_dir_format, show_header=self._show_header, show_header_if_empty=self._show_header_if_empty, title=title)
        t.set_column_title(**self.PACKAGE_DIR_HEADER_DICT)
        for row_d in rows:
            t.add_row(**row_d)
        t.render(PRINT)

    def info(self):
        PRINT(Table.format_title("Session {0} at {1}".format(self.session_name, self.session_root)))
        PRINT("name          : {0}".format(self.session_name))
        PRINT("type          : {0}".format(self.session_type))
        PRINT("description   : {0}".format(self.session_description))
        PRINT("read-only     : {0}".format(self.session_read_only))
        PRINT("creation time : {0}".format(self.session_creation_time))
        self.show_package_directories(show_title=True)
        #packages_list_string = self.session_config['packages']['loaded_packages']
        self.show_loaded_packages(show_title=True)

    def translate(self, translator):
        for var_name, var_value in self._environment.changeditems():
            orig_var_value = self._orig_environment.get(var_name, None)
            if var_value is None and orig_var_value is not None:
                # removed
                translator.var_unset(var_name)
            elif var_value != orig_var_value:
                # set
                translator.var_set(var_name, var_value)
        loaded_packages = ':'.join(self._loaded_packages.keys())
        translator.var_set("ZAPPER_LOADED_PACKAGES", loaded_packages)
        if self._deleted:
            translator.var_unset("ZAPPER_SESSION")
        else:
            translator.var_set("ZAPPER_SESSION", self.session_root)

    def translate_stream(self, translator, stream=None, translation_filename=None, *, dry_run=None):
        if dry_run is None:
            dry_run = self._dry_run
        self.translate(translator)
        if not dry_run:
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

    def check_directories(self, directories):
        dirs = {self._normpath(d) for d in string_to_list(directories)}
        orphans = set()
        for package in self._loaded_packages.values():
            d = self._normpath(package._package_dir)
            if not d in dirs:
                orphans.add(package.absolute_label)
        if orphans:
            LOGGER.error("cannot set directories={!r}: will leave {} orphan packages: {}".format(directories, len(orphans), list_to_string(orphans)))
            return False
        else:
            return True
