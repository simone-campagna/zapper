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

__all__ = ['Registry', 'MetaRegister', 'Register']

class BaseRegistry(object):
    __dict_factory__ = dict
    def __init__(self):
        self._registry = self.__dict_factory__()

    @abc.abstractmethod
    def register(self, instance, key):
        pass

    def __getitem__(self, key):
        return self._registry[key]

    def __contains__(self, key):
        return key in self._registry

    def __len__(self):
        return len(self._registry)

    def __iter__(self):
        return iter(self._registry)

    def keys(self):
        return self._registry.keys()

    def values(self):
        return self._registry.values()

    def items(self):
        return self._registry.items()

    def __str__(self):
        return str(self._registry)

    def __repr__(self):
        return repr(self._registry)

class ListRegistry(BaseRegistry):
    __dict_factory__ = lambda x : collections.defaultdict(list)

    def register(self, instance, key):
        self[key].append(instance)

class UniqueRegistry(BaseRegistry):
    def register(self, instance, key):
        assert not key in self
        self[key] = instance

class MetaRegister(abc.ABCMeta):
    def __new__(mcls, class_name, class_bases, class_dict):
        cls = super().__new__(mcls, class_name, class_bases, class_dict)
        if getattr(cls, '__registry__', None) is None:
            cls.__registry__ = collections.defaultdict(cls.__registry_factory__)
        return cls

class BaseRegister(metaclass=MetaRegister):
    __registry_factory__ = BaseRegistry
    __registry__ = None
    
    @abc.abstractmethod
    def register(self):
        pass

    def register_keys(self, **n_args):
        for key, value in n_args.items():
            self.__registry__[key].register(self, value)

    @classmethod
    def registry(cls, key):
        return cls.__registry__[key]

    @classmethod
    def registered_entry(cls, key, value):
        return cls.__registry__[key][value]

class ListRegister(BaseRegister):
    __registry_factory__ = ListRegistry
    __registry__ = None

class UniqueRegister(BaseRegister):
    __registry_factory__ = UniqueRegistry
    __registry__ = None

