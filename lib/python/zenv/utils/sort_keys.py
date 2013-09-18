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

class SortKeys(object):
    REVERSE = {'+': False, '-': True}
    def __init__(self, s, dct, label):
        self.keys = []
        for key in s.split(':'):
            if not key:
                continue
            if key[0] in '+-':
                sign = key[0]
                key = key[1:]
            else:
                sign = '+'
            if not key in dct:
                raise ValueError("invalid {} sort key {!r}".format(label, key))
            self.keys.append((sign, key))

    def sort(self, list_of_dicts):
        for sign, key in reversed(self.keys):
            list_of_dicts.sort(key=lambda x: x.get(key, ''), reverse=self.REVERSE[sign])

    def __str__(self):
        keys = []
        for sign, key in self.keys:
            if sign == '-':
                keys.append('-{}'.format(key))
            else:
                keys.append(key)
        return "{}({})".format(self.__class__.__name__, ":".join(keys))
