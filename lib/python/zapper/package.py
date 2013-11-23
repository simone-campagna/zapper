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

import re
import abc
import collections

from .transition import *
from .version import Version
from .registry import ListRegister
from .source_base import SourceBase
from .product import Product
from .package_expressions import NAME, PACKAGE, HAS_TAG
from .tag import Tag
from .expression import Expression, ConstExpression
from .text import fill
from .utils.table import show_table, show_title
from .utils.debug import PRINT, LOGGER


__all__ = ['Package']


class Package(ListRegister, SourceBase, Transition):
    __version_factory__ = Version
    __registry__ = None
    SUITE_SEPARATOR = '/'
    VERSION_SEPARATOR = '-'
    RE_VALID_NAME = re.compile("[a-zA-Z_]\w*")
    def __init__(self, product, version, *, short_description=None, long_description=None, product_conflict=True, suite=None):
        super().__init__()
        if isinstance(product, str):
            product_name = product
            product = Product.get_product(product_name)
            if product is None:
                raise ValueError("undefined product {}".format(product_name))
        else:
            assert isinstance(product, Product)
        self._product = product
        if version is None:
            version = ''
        if not isinstance(version, Version):
            version = self.make_version(version)
        self._name = self._product._name
        self._version = version
        self._category = self._product._category
        self._short_description = short_description
        self._long_description = long_description
        if suite is None:
            from .suite import ROOT
            suite = ROOT
        else:
            from .suite import Suite
            assert isinstance(suite, Suite)
        self._suite = suite
        self._transitions = []
        self._requirements = []
        self._preferences = []
        self._conflicts = []
        self._tags = set()
        self._suite.add_package(self)
        if self._version:
            suffix = self.VERSION_SEPARATOR + self._version
        else:
            suffix = ''
        self._label = self._name + suffix
        if self._suite is self:
            self._absolute_name = self._name
            self._labels = ('', )
        else:
            self._absolute_name = "{0}{1}{2}".format(self._suite._absolute_label, self.SUITE_SEPARATOR, self._name)
            self._labels = self._suite._labels + (self._label, )
        self._absolute_label = self._absolute_name + suffix
        self.register()
        if product_conflict:
            self.conflicts(NAME == self._name)

    def labels(self):
        return self._labels

    def package_type(self):
        return "package"

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def category(self):
        return self._category

    @property
    def label(self):
        return self._label

    @property
    def absolute_label(self):
        return self._absolute_label

    @property
    def absolute_name(self):
        return self._absolute_name

    @property
    def suite(self):
        return self._suite

    def product(self):
        return self._product

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
            return self._product.short_description
    
    def set_short_description(self, short_description):
        self._short_description = short_description

    short_description = property(get_short_description, set_short_description)
   
    def get_long_description(self):
        if self._long_description:
            return self._long_description
        else:
            return self._product.long_description

    def set_long_description(self, long_description):
        self._long_description = long_description

    long_description = property(get_long_description, set_long_description)

    def show_content(self):
        show_title("{0} {1}".format(self.__class__.__name__, self._label))
        PRINT("name           : {0}".format(self._name))
        PRINT("version        : {0}".format(self._version))
        PRINT("category       : {0}".format(self._category))
        PRINT("suite          : {0}".format(self._suite._absolute_label))
        PRINT("absolute label : {0}".format(self._absolute_label))
        PRINT("directory      : {0}".format(self.source_dir))
        PRINT("file           : {0}".format(self.source_file))
        PRINT("module         : {0}".format(self.source_module))
        show_table("Transitions", self.get_transitions())
        show_table("Requirements", self.get_requirements())
        show_table("Preferences", self.get_preferences())
        show_table("Conflicts", self.get_conflicts())

    def show(self):
        self.show_content()
        if self.short_description:
            show_title("Short description")
            PRINT(fill(self.short_description))
        if self.long_description:
            show_title("Long description")
            PRINT(fill(self.long_description))

    def make_version(self, version_string):
        return self.__version_factory__(version_string)

    def add_tag(self, tag):
        if not isinstance(tag, Tag):
            tag = Tag(tag)
        self._tags.add(tag)

    def has_tag(self, tag):
        return tag in self._tags

    def add_conflicting_tag(self, tag):
        self.add_tag(tag)
        self._conflicts.append(HAS_TAG(tag))

    @property
    def tags(self):
        return iter(self._tags)

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
        packages = tuple(packages)
        unmatched = []
        matched = []
        matched_d = collections.defaultdict(list)
        for expression in expressions:
            found = False
            for package in packages:
                if package is self:
                    # a package cannot require/prefer itself
                    continue
                expression.bind(package)
                if expression.get_value():
                    #matched.append((self, expression, package))
                    #input("... {0} vs {1} [{2}]".format(self, package, expression))
                    matched_d[(package.product(), expression)].append(package)
                    found = True
            if not found:
                unmatched.append((self, expression))
        for (product, expression), matching_packages in matched_d.items():
            matching_packages.sort(key=lambda package: package._version)
            matched.append((self, expression, matching_packages))
        return matched, unmatched

    def match_requirements(self, packages):
        return self.match_expressions(packages, self._requirements)

    def match_preferences(self, packages):
        return self.match_expressions(packages, self._preferences)

    def match_conflicts(self, packages):
        conflicts = self._match_conflicts(packages)
        for package in packages:
            conflicts.extend(package._match_conflicts([self]))
        return conflicts
        
    def _match_conflicts(self, loaded_packages):
        conflicts = []
        for expression in self._conflicts:
            for loaded_package in loaded_packages:
                if loaded_package is self:
                    # a package cannot conflicts with itself
                    continue
                expression.bind(loaded_package)
                if expression.get_value():
                    conflicts.append((self, expression, loaded_package))
        return conflicts

    @classmethod
    def filter(cls, packages, expression):
        for package in packages:
            expression.bind(package)
            if expression.get_value():
                yield package
 
    def register(self):
        self.register_keys(package_dir=self.source_dir)

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
        LOGGER.debug("{0}[{1}]: applying...".format(self.__class__.__name__, self))
        for transition in self._transitions:
            transition.apply(session)

    def revert(self, session):
        LOGGER.debug("{0}[{1}]: reverting...".format(self.__class__.__name__, self))
        for transition in self._transitions:
            transition.revert(session)

    def __repr__(self):
        return "{0}(name={1!r}, version={2!r}, category={3!r})".format(self.__class__.__name__, self._name, self._version, self._category)

    def __str__(self):
        return self.absolute_label

