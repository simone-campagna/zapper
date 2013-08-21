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

import abc
import collections

from .transition import *
from .version import Version
from .registry import ListRegister
from .package_family import PackageFamily
from .expression import Expression, AttributeGetter, InstanceGetter, ConstExpression
from .text import fill
from .utils.show_table import show_table, show_title
from .utils.debug import PRINT

__all__ = ['Package', 'NAME', 'VERSION', 'CATEGORY', 'PACKAGE']

NAME = AttributeGetter('name', 'NAME')
VERSION = AttributeGetter('version', 'VERSION')
CATEGORY = AttributeGetter('category', 'CATEGORY')
PACKAGE = InstanceGetter('PACKAGE')

class Package(ListRegister, Transition):
    __version_factory__ = Version
    __package_dir__ = None
    __registry__ = None
    def __init__(self, package_family, version, *, short_description=None, long_description=None, suite=None):
        super().__init__()
        assert isinstance(package_family, PackageFamily)
        self._package_family = package_family
        if not isinstance(version, Version):
            version = self.make_version(version)
        self.name = self._package_family.name
        self.version = version
        self.category = self._package_family.category
        self._short_description = short_description
        self._long_description = long_description
        if suite is None:
            from .suite import ROOT
            suite = ROOT
        self._package_dir = self.__package_dir__
        self._transitions = []
        self._requirements = []
        self._preferences = []
        self._conflicts = []
        self.register()

    def package_family(self):
        return self._package_family

    @classmethod
    def set_package_dir(cls, package_dir):
        cls.__package_dir__ = package_dir

    @classmethod
    def unset_package_dir(cls):
        cls.__package_dir__ = None

    def get_transitions(self):
        for transition in self._transitions:
            yield transition

    def get_requirements(self):
        for requirement in self._requirements:
            yield requirement

    def get_preferences(self):
        for preference in self._preferences:
            yield preference

    def get_conflicts(self):
        for conflict in self._conflicts:
            yield conflict

    def get_short_description(self):
        if self._short_description:
            return self._short_description
        else:
            return self._package_family.short_description
    
    def set_short_description(self, short_description):
        self._short_description = short_description

    short_description = property(get_short_description, set_short_description)
   
    def get_long_description(self):
        if self._long_description:
            return self._long_description
        else:
            return self._package_family.long_description

    def set_long_description(self, long_description):
        self._long_description = long_description

    long_description = property(get_long_description, set_long_description)

    def show(self):
        show_title("Package {0}".format(self.label()))
        PRINT("name     : {0}".format(self.name))
        PRINT("version  : {0}".format(self.version))
        PRINT("category : {0}".format(self.category))
        show_table("Transitions", self.get_transitions())
        show_table("Requirements", self.get_requirements())
        show_table("Preferences", self.get_preferences())
        show_table("Conflicts", self.get_conflicts())
        if self.short_description:
            show_title("Short description")
            PRINT(fill(self.short_description))
        if self.long_description:
            show_title("Long description")
            PRINT(fill(self.long_description))

    def make_version(self, version_string):
        return self.__version_factory__(version_string)

    def label(self):
        return "{0}/{1}".format(self.name, self.version)

    def _create_expression(self, *expressions):
        result = None
        for e in expressions:
            if isinstance(e, Package):
                expression = PACKAGE == e
            elif isinstance(e, str):
                expression = NAME == e
            elif isinstance(e, Expression):
                expression = e
            else:
                expression = ConstExpression(e)
            if result is None:
                result = expression
            else:
                result = result & expression
        return result
        
    def requires(self, expression, *expressions):
        self._requirements.append(self._create_expression(expression, *expressions))

    def prefers(self, expression, *expressions):
        self._preferences.append(self._create_expression(expression, *expressions))

    def conflicts(self, expression, *expressions):
        self._conflicts.append(self._create_expression(expression, *expressions))

    def match_expressions(self, packages, expressions):
        unmatched = []
        matched = []
        matched_d = collections.defaultdict(list)
        for expression in expressions:
            found = False
            for package in packages:
                expression.bind(package)
                if expression.get_value():
                    #matched.append((self, expression, package))
                    matched_d[package.package_family()].append((self, expression, package))
                    found = True
            if not found:
                unmatched.append((self, expression))
        for package_family, lst in matched_d.items():
            lst.sort(key=lambda t: t[-1].version)
            matched.append(lst[-1])
        return matched, unmatched

    def match_requirements(self, package):
        return self.match_expressions(package, self._requirements)

    def match_preferences(self, package):
        return self.match_expressions(package, self._preferences)

    def match_conflicts(self, packages):
        conflicts = self._match_conflicts(packages)
        for package in packages:
            conflicts.extend(package._match_conflicts([self]))
        return conflicts
        
    def _match_conflicts(self, loaded_packages):
        conflicts = []
        for expression in self._conflicts:
            for loaded_package in loaded_packages:
                expression.bind(loaded_package)
                if expression.get_value():
                    conflicts.append((self, expression, package))
        return conflicts

    def register(self):
        self.register_keys(package_dir=self._package_dir)

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

