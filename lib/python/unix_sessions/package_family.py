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

from .category import Category
from .registry import Register

class PackageFamily(Register):
    def __init__(self, name, category, short_description="", long_description=""):
        if not isinstance(name, str):
            name = str(name)
        if ':' in name:
            raise ValueError("invalid package name {0}: cannot contain ':'".format(name))
        if not isinstance(category, Category):
            category = Category(category)
        self._name = name
        self._category = category
        self.short_description = short_description
        self.long_description = long_description

    @property
    def name(self):
        return self._name

    @property
    def category(self):
        return self._category

    def get_short_description(self):
        return self._short_description

    def set_short_description(self, short_description):
        self._short_description = short_description

    short_description = property(get_short_description, set_short_description)

    def get_long_description(self):
        return self._long_description

    def set_long_description(self, long_description):
        self._long_description = long_description

    long_description = property(get_long_description, set_long_description)

    def register(self):
        self.register_keys(name=self._name)

