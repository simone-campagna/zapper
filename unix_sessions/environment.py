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
        super().__init__(init)
        
    def set_var(self, var_name, var_value):
        assert isinstance(var_name, str)
        assert isinstance(var_value, str)
        self[var_name] = var_value

    def _split_and_remove(self, var_name, var_value, separator):
        return [item for item in self.get(var_name, '').split(separator) if item != var_value]

    def prepend_var(self, var_name, var_value, separator=':'):
        l = self._split_and_remove(var_name, var_value, separator)
        l.insert(var_value, 0)
        self[var_name] = separator.join(l)

    def append_var(self, var_name, var_value, separator=':'):
        l = self._split_and_remove(var_name, var_value, separator)
        l.append(var_value)
        self[var_name] = separator.join(l)

