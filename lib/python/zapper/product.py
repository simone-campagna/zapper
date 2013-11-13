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

import re
import abc

from .category import Category
from .registry import UniqueRegister
from .parameters import PARAMETERS

class Product(UniqueRegister):
    RE_VALID_NAME = re.compile("|[a-zA-Z_][a-zA-z_0-9\.]*")
    def __new__(cls, name, category, *, short_description=None, long_description=None):
        name_registry = cls.registry('name')
        #print("***", cls, repr(name), name in name_registry, name_registry)
        if name in name_registry:
            instance = name_registry[name]
            for key, val in (('category', category),
                             ('short_description', short_description),
                             ('long_description', long_description)):
                existing_val = getattr(instance, key)
                if val is not None and existing_val != val:
                    raise ValueError("invalid {key!r} value {val!r} for existing product {product!r}: already defined as {existing_val!r} in {existing_filename!r}".format(
                        key=key, val=val, product=name, existing_val=existing_val, existing_filename=instance.product_file))
        else:
            if not cls.RE_VALID_NAME.match(name):
                raise ValueError("invalid product name {!r}".format(name))
            if short_description is None:
                short_description = ""
            if long_description is None:
                long_description = ""
            if not isinstance(name, str):
                name = str(name)
            #for ch in cls.INVALID_CHARACTERS:
            #    if ch in name:
            #        raise ValueError("invalid package name {0}: cannot contain {1!r}".format(name, cls.INVALID_CHARACTERS))
            instance = super().__new__(cls)
            if not isinstance(category, Category):
                category = Category(category)
            instance._name = name
            instance._category = category
            instance.short_description = short_description
            instance.long_description = long_description
            instance.register()
            instance._product_dir = PARAMETERS.current_dir
            instance._product_file = PARAMETERS.current_file
            instance._product_module = PARAMETERS.current_module
        return instance

    @property
    def product_dir(self):
        return self._product_dir

    @property
    def product_file(self):
        return self._product_file

    @property
    def product_module(self):
        return self._product_module

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

