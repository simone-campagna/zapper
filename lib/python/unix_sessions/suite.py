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

from .package import Package
from .suite_family import SuiteFamily
from .utils.show_table import show_table, show_title


import abc

__all__ = ['Suite', 'ROOT']

class Suite(Package):
    def __init__(self, suite_family, version, *, short_description=None, long_description=None, suite=None):
        if isinstance(suite_family, str):
            suite_family = SuiteFamily.get_family(suite_family)
        assert isinstance(suite_family, SuiteFamily)
        self._packages = []
        super().__init__(suite_family, version, short_description=short_description, long_description=long_description, suite=suite)

    def packages(self):
        return iter(self._packages)

    def add_package(self, package):
        assert isinstance(package, Package)
        if package is not self:
            self._packages.append(package)
            self.add_package_requirement(package)

    def add_package_requirement(self, package):
        package.requires(self)

    def apply(self, session):
        for package in self._packages:
            package.apply(session)

    def show_content(self):
        super().show_content()
        show_table("Packages", self.packages())

class _RootSuite(Suite):
    def __init__(self):
        suite_family = SuiteFamily.get_family('ROOT')
        version = '0'
        short_description = 'The Root suite'
        long_description = 'The Root suite contains all available suites/packages'
        super().__init__(suite_family, version, short_description=short_description, long_description=long_description, suite=self)

    def add_package_requirement(self, package):
        pass

ROOT = _RootSuite()

