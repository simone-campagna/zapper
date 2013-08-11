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

from .component import Component
from .version import Version
#from .category import Category

import abc

__all__ = ['Package']

class Package(Component):
    def __init__(self, name, version, category):
        if not isinstance(name, str):
            name = str(name)
        if not isinstance(version, Version):
            version = Version(version)
        if not isinstance(category, str):
            category = str(category)
        self.name = name
        self.version = version
        self.category = category
        super().__init__()
        self._requirements = []
        self._preferences = []
        self._conflicts = []

    def __filters(self, *filters):
        flt_funcs = []
        for flt in filters:
            if isinstance(flt, str):
                def create_func(flt):
                    return lambda package: package.name == flt
                flt_func = create_func(flt)
            elif isinstance(flt, Version):
                def create_func(flt):
                    return lambda package: package.version == flt
                flt_func = create_func(flt)
            else:
                flt_func = flt
            flt_funcs.append(flt_func)
        return flt_funcs

    def requires(self, *filters):
        self._requirements.append(self.__filters(filters))

    def prefers(self, *filters):
        self._preferences.append(self.__filters(filters))

    def conflicts(self, *filters):
        self._conflicts.append(self.__filters(filters))

