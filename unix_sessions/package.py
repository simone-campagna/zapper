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

from .transition import *
from .version import Version
from .registry import Registry

import abc

__all__ = ['Package']

class Package(Transition):
    REGISTRY = Registry()
    __version_class__ = Version
    def __init__(self, name, version, category):
        if not isinstance(name, str):
            name = str(name)
        if not isinstance(version, Version):
            version = self.make_version(version)
        if not isinstance(category, str):
            category = str(category)
        self.name = name
        self.version = version
        self.category = category
        self._transitions = []
        self._requirements = []
        self._preferences = []
        self._conflicts = []
        self.register()

    def make_version(self, version_string):
        return self.__version_class__(version_string)

    def label(self):
        return "{0}/{1}".format(self.name, self.version)

    def __filters(self, *filters):
        flt_funcs = []
        for flt in filters:
            if isinstance(flt, str):
                package_name = flt
                def create_func(package_name):
                    return lambda package: package.name == package_name
                flt_func = create_func(package_name)
            elif isinstance(flt, Version):
                package_version = flt
                def create_func(package_version):
                    return lambda package: package.version == package_version
                flt_func = create_func(package_version)
            else:
                flt_func = flt
            flt_funcs.append(flt_func)
        def create_func(*flt_funcs):
            def filter(package):
                for flt in flt_funcs:
                    if not flt(package):
                        return False
                return True
        return create_func(*flt_funcs)

    def requires(self, *filters):
        self._requirements.append(self.__filters(filters))

    def prefers(self, *filters):
        self._preferences.append(self.__filters(filters))

    def conflicts(self, *filters):
        self._conflicts.append(self.__filters(filters))

    def register(self):
        self.__class__.REGISTRY.register(self)

    def add_transition(self, transition):
        assert isinstance(transition, Transition)
        self._transitions.append(transition)
        
    def var_set(self, var_name, var_value):
        self.add_transition(SetEnv(var_name, var_value))

    def var_unset(self, var_name):
        self.add_transition(UnsetEnv(var_name))

    def list_prepend(self, var_name, var_value, separator=None):
        self.add_transition(PrependList(var_name, var_value, separator))

    def path_prepend(self, var_name, var_value, separator=None):
        self.add_transition(PrependPath(var_name, var_value, separator))

    def list_append(self, var_name, var_value, separator=None):
        self.add_transition(AppendList(var_name, var_value, separator))

    def path_append(self, var_name, var_value, separator=None):
        self.add_transition(AppendPath(var_name, var_value, separator))

    def list_remove(self, var_name, var_value, separator=None):
        self.add_transition(RemoveList(var_name, var_value, separator))

    def path_remove(self, var_name, var_value, separator=None):
        self.add_transition(RemovePath(var_name, var_value, separator))

    def apply(self, session):
        for transition in self._transitions:
            transition.apply(session)

    def revert(self, session):
        for transition in self._transitions:
            transition.revert(session)

    def __repr__(self):
        return "{0}(name={1!r}, version={2!r}, category={3!r})".format(self.__class__.__name__, self.name, self.version, self.category)

    def __str__(self):
        return self.label()
