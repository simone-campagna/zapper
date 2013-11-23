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
from .product import Product
from .package_expressions import NAME, PACKAGE, HAS_TAG
from .tag import Tag
from .expression import Expression, ConstExpression
from .text import fill
from .utils.table import show_table, show_title
from .utils.debug import PRINT, LOGGER
from .pp_common_base import PPCommonBase


__all__ = ['Package']


class Package(ListRegister, PPCommonBase):
    __version_factory__ = Version
    __registry__ = None
    SUITE_SEPARATOR = '/'
    VERSION_SEPARATOR = '-'
    RE_VALID_NAME = re.compile("[a-zA-Z_]\w*")
    def __init__(self, product, version, *, short_description=None, long_description=None, suite=None, inherit=True):
        super().__init__()
        PPCommonBase.__init__(self)
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
        if isinstance(inherit, dict):
            self._inherit_requirements = inherit.get('requirements', True)
            self._inherit_preferences = inherit.get('preferences', True)
            self._inherit_conflicts = inherit.get('conflicts', True)
            self._inherit_transitions = inherit.get('transitions', True)
        else:
            inherit = bool(inherit)
            self._inherit_requirements = inherit
            self._inherit_preferences = inherit
            self._inherit_conflicts = inherit
            self._inherit_transitions = inherit
        #if product_conflict:
        #    self.conflicts(NAME == self._name)
        self.pre_load_hook = None
        self.post_load_hook = None
        self.pre_unload_hook = None
        self.post_unload_hook = None

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

    @property
    def product(self):
        return self._product

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

    def get_transitions(self):
        if self._inherit_transitions:
            for transition in self._product.get_transitions():
                yield transition
        for transition in super().get_transitions():
            yield transition

    def get_requirements(self):
        if self._inherit_requirements:
            for requirement in self._product.get_requirements():
                yield requirement
        for requirement in super().get_requirements():
            yield requirement
        
    def get_preferences(self):
        if self._inherit_preferences:
            for preference in self._product.get_preferences():
                yield preference
        for preference in super().get_preferences():
            yield preference
        
    def get_conflicts(self):
        if self._inherit_conflicts:
            for conflict in self._product.get_conflicts():
                yield conflict
        for conflict in super().get_conflicts():
            yield conflict
        
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
                    matched_d[(package.product, expression)].append(package)
                    found = True
            if not found:
                unmatched.append((self, expression))
        for (product, expression), matching_packages in matched_d.items():
            matching_packages.sort(key=lambda package: package._version)
            matched.append((self, expression, matching_packages))
        return matched, unmatched

    @classmethod
    def filter(cls, packages, expression):
        for package in packages:
            expression.bind(package)
            if expression.get_value():
                yield package
 
    def register(self):
        self.register_keys(package_dir=self.source_dir)

    def set_pre_load_hook(self, hook):
        self.pre_load_hook = hook

    def set_post_load_hook(self, hook):
        self.post_load_hook = hook

    def set_pre_unload_hook(self, hook):
        self.pre_unload_hook = hook

    def set_post_unload_hook(self, hook):
        self.post_unload_hook = hook

    def exec_hook(self, hook_name, hook, session):
        if hook is not None:
            try:
                hook(self, session)
            except Exception as e:
                LOGGER.warning("{} hook failed: {}: {}".format(hook_name, e.__class__.__name__, e))

    def exec_pre_load_hook(self, session):
        self.exec_hook('pre_load', self.pre_load_hook, session)

    def exec_post_load_hook(self, session):
        self.exec_hook('post_load', self.post_load_hook, session)

    def exec_pre_unload_hook(self, session):
        self.exec_hook('pre_unload', self.pre_unload_hook, session)

    def exec_post_unload_hook(self, session):
        self.exec_hook('post_unload', self.post_unload_hook, session)

    def load(self, session, *, info=True):
        if info and self.pre_load_hook is not None:
            self.exec_pre_load_hook(session)
        self.apply(session)
        if info and self.post_load_hook is not None:
            self.exec_post_load_hook(session)

    def unload(self, session, *, info=True):
        if info and self.pre_unload_hook is not None:
            self.exec_pre_unload_hook(session)
        self.revert(session)
        if info and self.post_unload_hook is not None:
            self.exec_post_unload_hook(session)

    def make_self_expression(self):
        print("PACK", self.__class__, self)
        return PACKAGE == self

    def __repr__(self):
        return "{0}(name={1!r}, version={2!r}, category={3!r})".format(self.__class__.__name__, self._name, self._version, self._category)

    def __str__(self):
        return self.absolute_label

