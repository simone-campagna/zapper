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

class Registry(collections.defaultdict):
    def __init__(self):
        super().__init__(list)

    def register(self, instance, key):
        self[key].append(instance)

class MetaRegister(abc.ABCMeta):
    def __new__(mcls, class_name, class_bases, class_dict):
        cls = super().__new__(mcls, class_name, class_bases, class_dict)
        if getattr(cls, '__registry__', None) is None:
            cls.__registry__ = collections.defaultdict(Registry)
        return cls

class Register(metaclass=MetaRegister):
    __registry__ = None
    
    @abc.abstractmethod
    def register(self):
        pass

    def register_keys(self, **n_args):
        for key, value in n_args.items():
            self.__registry__[key][value].append(self)

    @classmethod
    def registry(cls, key):
        return cls.__registry__[key]

    @classmethod
    def registered_instances(cls, key, value):
        return cls.__registry__[key][value]

