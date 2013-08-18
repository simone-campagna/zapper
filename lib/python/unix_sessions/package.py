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
from .expression import Expression, AttributeGetter, ConstExpression
from .text import fill
from .utils.show_table import show_table, show_title
from .utils.debug import PRINT

import abc

__all__ = ['Package', 'NAME', 'VERSION', 'CATEGORY']

NAME = AttributeGetter('name', 'NAME')
VERSION = AttributeGetter('version', 'VERSION')
CATEGORY = AttributeGetter('category', 'CATEGORY')

class Category(str):
    __categories__ = ['application', 'tool', 'library', 'compiler']
    def __init__(self, value):
        if not value in self.__categories__:
            raise KeyError("invalid category {0!r}".format(value))
        super().__init__(value)

    @classmethod
    def add_category(cls, category):
        if not category in cls.__categories__:
            cls.__categories__.append(category)

class Package(Transition):
    __registry__ = Registry()
    __version_class__ = Version
    def __init__(self, name, version, category, short_description="", long_description=""):
        if not isinstance(name, str):
            name = str(name)
        if ':' in name:
            raise ValueError("invalid package name {0}: cannot contain ':'".format(name))
        if not isinstance(version, Version):
            version = self.make_version(version)
        if not isinstance(category, Category):
            category = Category(category)
        self.name = name
        self.version = version
        self.category = category
        self.short_description = short_description
        self.long_description = long_description
        self._transitions = []
        self._requirements = []
        self._preferences = []
        self._conflicts = []
        self.register()

    @classmethod
    def set_module_dir(cls, module_dir):
        cls.__registry__.set_default_key(module_dir)

    @classmethod
    def unset_module_dir(cls):
        cls.__registry__.unset_default_key()

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

    def set_short_description(self, short_description):
        self.short_description = short_description

    def set_long_description(self, long_description):
        self.long_description = long_description

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
        return self.__version_class__(version_string)

    def label(self):
        return "{0}/{1}".format(self.name, self.version)

#    def __filters(self, *filters):
#        flt_funcs = []
#        for flt in filters:
#            if isinstance(flt, str):
#                package_name = flt
#                def create_func(package_name):
#                    return lambda package: package.name == package_name
#                flt_func = create_func(package_name)
#            elif isinstance(flt, Version):
#                package_version = flt
#                def create_func(package_version):
#                    return lambda package: package.version == package_version
#                flt_func = create_func(package_version)
#            else:
#                flt_func = flt
#            flt_funcs.append(flt_func)
#        def create_func(*flt_funcs):
#            def filter(package):
#                for flt in flt_funcs:
#                    if not flt(package):
#                        return False
#                return True
#            return filter
#        return create_func(*flt_funcs)

    def _create_expression(self, *expressions):
        result = None
        for e in expressions:
            if isinstance(e, str):
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

    def match_expressions(self, loaded_packages, expressions):
        unmatched = []
        matched = []
        for expression in expressions:
            for loaded_package in loaded_packages:
                expression.bind(loaded_package)
                if expression.get_value():
                    matched.append((self, expression, loaded_package))
                    break
            else:
                unmatched.append((self, expression))
        return matched, unmatched

    def match_requirements(self, package):
        return self.match_expressions(package, self._requirements)

    def match_preferences(self, package):
        return self.match_expressions(package, self._preferences)

    def match_conflicts(self, loaded_packages):
        conflicts = self._match_conflicts(loaded_packages)
        for loaded_package in loaded_packages:
            conflicts.extend(loaded_package._match_conflicts([self]))
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
        self.__class__.__registry__.register(self)

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
