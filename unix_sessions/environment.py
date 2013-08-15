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
import os

class Environment(dict):
    def __init__(self, init=None):
        if init is None:
            init = os.environ
        self._changedkeys = set()
        super().__init__(init)
        
    def __setitem__(self, var_name, var_value):
        cur_value = self.get(var_name, None)
        if cur_value is None or cur_value != var_value:
            self._changedkeys.add(var_name)
            super().__setitem__(var_name, var_value)

    def __delitem__(self, var_name):
        cur_value = self.get(var_name, None)
        if cur_value is not None:
            self._changedkeys.add(var_name)
            super().__delitem__(var_name)

    def changedkeys(self):
        for key in self._changedkeys:
            yield key

    def changedvalues(self):
        for key in self._changedkeys:
            yield self.get(key, None)

    def changeditems(self):
        for key in self._changedkeys:
            yield key, self.get(key, None)

    def var_get(self, var_name):
        return self.get(var_name, None)

    def _var_split(self, transform, var_name, separator):
        return (transform(item) for item in self.get(var_name, '').split(separator))

    def _var_split_uniq(self, transform, var_name, var_value, separator):
        for item in self._var_split(transform, var_name, separator):
            if item != var_value:
                yield item

    def _list_prepend(self, transform, var_name, var_value, separator=None):
        if separator is None:
            separator = ':'
        var_value = transform(var_value)
        l = list(self._var_split_uniq(transform, var_name, var_value, separator))
        l.insert(var_value, 0)
        self[var_name] = separator.join(l)

    def _list_append(self, transform, var_name, var_value, separator=':'):
        if separator is None:
            separator = ':'
        var_value = transform(var_value)
        l = list(self._var_split_uniq(transform, var_name, var_value, separator))
        l.append(var_value)
        self[var_name] = separator.join(l)

    def _list_insert(self, transform, var_name, var_value, var_template, separator=None):
        """_list_insert(var_name, var_value, var_template, separator=None) -> try to insert var_value in list var_name, in the same position as in var_template"""
        if separator is None:
            separator = ':'
        var_value = transform(var_value)
        l = list(self._var_split_uniq(transform, var_name, var_value, separator))
        c = list(self._var_split(transform, var_name, separator))
        
        l_index = 0
        if var_value in c:
            c_index = c.index(var_value)
            if c_index >= 0 and c[c_index - 1] in l:
                l_index = l.index(c[c_index - 1]) + 1
            elif c_index < len(c) - 1 and c[c_index + 1] in l:
                l_index = l.index(c[c_index + 1]) - 1
        l.insert(l_index, var_value)
        self[var_name] = separator.join(l)

    def _list_remove(self, transform, var_name, var_value, separator=':'):
        l = list(self._var_split_uniq(transform, var_name, var_value, separator))
        self[var_name] = separator.join(l)
  
    def IDENTITY(self, var_value):
        return var_value

    def NORMPATH(self, var_value):
        return os.path.normpath(var_value)

    def var_set(self, var_name, var_value):
        assert isinstance(var_name, str)
        assert isinstance(var_value, str)
        self[var_name] = var_value

    def var_unset(self, var_name):
        if var_name in self:
            print("HERE unset ", var_name)
            del self[var_name]

    def list_prepend(self, var_name, var_value, separator=None):
        self._list_prepend(self.IDENTITY, var_name, var_value, separator)

    def path_prepend(self, var_name, var_value, separator=None):
        self._list_prepend(self.NORMPATH, var_name, var_value, separator)

    def list_append(self, var_name, var_value, separator=None):
        self._list_append(self.IDENTITY, var_name, var_value, separator)

    def path_append(self, var_name, var_value, separator=None):
        self._list_append(self.NORMPATH, var_name, var_value, separator)

    def list_insert(self, var_name, var_value, var_template, separator=None):
        self._list_insert(self.IDENTITY, var_name, var_value, var_template, separator)

    def path_insert(self, var_name, var_value, var_template, separator=None):
        self._list_insert(self.NORMPATH, var_name, var_value, var_template, separator)

    def list_remove(self, var_name, var_value, separator=None):
        self._list_remove(self.IDENTITY, var_name, var_value, separator)

    def path_remove(self, var_name, var_value, separator=None):
        self._list_remove(self.NORMPATH, var_name, var_value, separator)
