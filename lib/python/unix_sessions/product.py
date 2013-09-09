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

__all__ = ['Product']

import abc

from .category import Category
from .registry import UniqueRegister

class Product(UniqueRegister):
    INVALID_CHARACTERS = '.:'
    def __new__(cls, name, category, *, short_description=None, long_description=None):
        name_registry = cls.registry('name')
        #print("***", cls, repr(name), name in name_registry, name_registry)
        if name in name_registry:
            instance = name_registry[name]
            for key, val in (('category', category),
                             ('short_description', short_description),
                             ('long_description', long_description)):
                if val is not None and getattr(instance, key) != val:
                    raise ValueError("invalid value {} = {!r} for existing product {}".format(key, val, name))
        else:
            if short_description is None:
                short_description = ""
            if long_description is None:
                long_description = ""
            if not isinstance(name, str):
                name = str(name)
            for ch in cls.INVALID_CHARACTERS:
                if ch in name:
                    raise ValueError("invalid package name {0}: cannot contain {1!r}".format(name, cls.INVALID_CHARACTERS))
            instance = super().__new__(cls)
            if not isinstance(category, Category):
                category = Category(category)
            instance._name = name
            instance._category = category
            instance.short_description = short_description
            instance.long_description = long_description
            instance.register()
        return instance

    @classmethod
    def get_product_names(cls):
        return (product_name for product_name in cls.registry('name'))

    @classmethod
    def has_product(cls, name, default=None):
        return name in cls.registry('name')

    @classmethod
    def get_product(cls, name, default=None):
        return cls.registry('name').get(name, default)

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

