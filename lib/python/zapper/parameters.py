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

__all__ = ['Parameters', 'PARAMETERS']

class Parameters(object):
    def __init__(self, current_dir=None, current_file=None, current_module=None):
        self._current_dir = current_dir
        self._current_file = current_file
        self._current_module = current_module

    def get_current_dir(self):
        return self._current_dir

    def set_current_dir(self, current_dir):
        self._current_dir = current_dir

    current_dir = property(get_current_dir, set_current_dir)

    def unset_current_dir(self):
        self._current_dir = None

    def get_current_file(self):
        return self._current_file

    def set_current_file(self, current_file):
        self._current_file = current_file

    current_file = property(get_current_file, set_current_file)

    def unset_current_file(self):
        self._current_file = None

    def get_current_module(self):
        return self._current_module

    def set_current_module(self, current_module):
        self._current_module = current_module

    current_module = property(get_current_module, set_current_module)

    def unset_current_module(self):
        self._current_module = None

    def set_current_module_file(self, current_module, current_file):
        self.set_current_module(current_module)
        self.set_current_file(current_file)

    def unset_current_module_file(self):
        self.unset_current_module()
        self.unset_current_file()

PARAMETERS = Parameters()

