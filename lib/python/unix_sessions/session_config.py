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

import os
import configparser

from .lock_file import Lock

class SessionConfig(configparser.ConfigParser):
    def __init__(self, filename=None):
        super().__init__()
        self.filename = filename
        if self.filename and os.path.lexists(self.filename):
            self.load()
        if not 'session' in self:
            self['session'] = {}
        if not 'name' in self['session']:
            self['session']['name'] = ''
        if not 'type' in self['session']:
            self['session']['type'] = ''
        if not 'packages' in self:
            self['packages'] = {}
        if not 'directories' in self['packages']:
            self['packages']['directories'] = ''
        if not 'loaded_packages' in self['packages']:
            self['packages']['loaded_packages'] = ''

    def load(self):
        with Lock(self.filename, "r") as f_in:
            self.read_file(f_in, self.filename)

    def store(self):
        with Lock(self.filename, "w") as f_out:
            self.write(f_out)

