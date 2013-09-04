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

__all__ = ['SuiteFamily']

import abc

from .package_family import PackageFamily

class SuiteFamily(PackageFamily):
    def __new__(cls, name, *, short_description=None, long_description=None):
        return super().__new__(cls, name, 'suite', short_description=short_description, long_description=long_description)

#    @classmethod
#    def get_family(cls, name):
#        name_registry = cls.registry('name')
#        if name in name_registry:
#            return name_registry[name]
#        else:
#            return SuiteFamily(name)
