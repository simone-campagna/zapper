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

__all__ = ['Registry']

class Registry(collections.defaultdict):
    def __init__(self):
        self.unset_default_key()
        super().__init__(list)

    def set_default_key(self, default_key):
        self._default_key = default_key

    def unset_default_key(self):
        self.set_default_key('default')

    def get_default_key(self):
        return self._default_key

    def register(self, instance, key=None):
        if key is None:
            key = self._default_key
        self[key].append(instance)

#    def __iter__(self):
#        print(":::---")
#        for key, lst in self.items():
#            print(":::", key, lst)
#            for instance in lst:
#                yield instance
#
#    def __len__(self):
#        return sum(len(lst) for lst in self.values())

#    def __iter__(self):
#        return iter(self._reg)
#
#    def __len__(self):
#        return len(self._reg)
