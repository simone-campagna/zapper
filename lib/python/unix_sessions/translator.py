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

import sys
import abc
import collections

class MetaTranslator(abc.ABCMeta):
    __registry__ = collections.OrderedDict()
    def __new__(mcls, class_name, class_bases, class_dict):
        cls = super().__new__(mcls, class_name, class_bases, class_dict)
        for attr_name in dir(cls):
            attr_value = getattr(cls, attr_name)
            if callable(attr_value) and hasattr(attr_value, '__isabstractmethod__'):
                break
        else:
            if hasattr(cls, '__registry_name__'):
                name = cls.__registry_name__
            else:
                name = cls.__name__
            mcls.__registry__[name] = cls
        return cls

    def createbyname(self, name):
        if name in self.__registry__:
            return self.__registry__[name]()
        else:
            raise KeyError("invalid translator: {0!r}".format(name))

class Translator(object, metaclass=MetaTranslator):
    def __init__(self):
        self._vars = []

    def var_set(self, var_name, var_value):
        self._vars.append((var_name, var_value))

    def var_unset(self, var_name):
        self._vars.append((var_name, None))

    def translate(self, stream=None):
        if stream is None:
            stream = sys.stdout
        for var_name, var_value in self._vars:
            if var_value is None:
                #print("TRANSLATION: unset({0!r})".format(var_name))
                self.translate_var_unset(stream, var_name)
            else:
                #print("TRANSLATION: set({0!r}, {1!r})".format(var_name, var_value))
                self.translate_var_set(stream, var_name, var_value)
        self.clear()

    def clear(self):
        del self._vars[:]

    @abc.abstractmethod
    def translate_var_unset(self, stream, var_name):
        pass

    @abc.abstractmethod
    def translate_var_set(self, stream, var_name, var_value):
        pass

    @abc.abstractmethod
    def translate_remove_filename(self, stream, filename):
        pass

    @abc.abstractmethod
    def translate_remove_empty_directory(self, stream, directory):
        pass

    @abc.abstractmethod
    def translate_remove_directory(self, stream, directory):
        pass

    def __repr__(self):
        return "{c}()".format(c=self.__class__.__name__)
    __str__ = __repr__
    

