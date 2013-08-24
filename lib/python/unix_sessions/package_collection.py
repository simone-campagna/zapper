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

import collections

from .utils.debug import LOGGER


class PackageCollection(collections.OrderedDict):
    def __init__(self):
        super().__init__(self)
        self._changed_package_full_labels = []

    def is_changed(self):
        return bool(self._changed_package_full_labels)

    def __setitem__(self, package_full_label, package):
        old_package = super().get(package_full_label, None)
        if old_package != package:
            self._changed_package_full_labels.append(package_full_label)
        super().__setitem__(package_full_label, package)
       
    def __delitem__(self, package_full_label):
        if package_full_label in self:
            self._changed_package_full_labels.append(package_full_label)
            super().__delitem__(package_full_label)

    def add_package(self, package):
        package_full_label = package.full_label()
        if package_full_label in self and self[package_full_label] is not package:
            #raise SessionError("package {0} hides {1}".format(package.full_label(), self[package_full_label].full_label()))
            LOGGER.warning("package {0} hides {1}".format(package.full_label(), self[package_full_label].full_label()))
        self[package_full_label] = package

    def remove_package(self, package):
        package_full_label = package.full_label()
        del self[package_full_label]

