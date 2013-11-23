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
        self._changed_package_absolute_labels = []

    def is_changed(self):
        return bool(self._changed_package_absolute_labels)

    def __setitem__(self, package_absolute_label, package):
        old_package = super().get(package_absolute_label, None)
        if old_package != package:
            self._changed_package_absolute_labels.append(package_absolute_label)
        super().__setitem__(package_absolute_label, package)
       
    def __delitem__(self, package_absolute_label):
        if package_absolute_label in self:
            self._changed_package_absolute_labels.append(package_absolute_label)
            super().__delitem__(package_absolute_label)

    def add_package(self, package):
        package_absolute_label = package.absolute_label
        if package_absolute_label in self and self[package_absolute_label].source_file != package.source_file:
            #raise SessionError("package {0} hides {1}".format(package.absolute_label, self[package_absolute_label].absolute_label))
            LOGGER.warning("package {} from {}:{} hides {} from {}:{}".format(
                package.absolute_label, package.source_dir, package.source_file, 
                self[package_absolute_label].absolute_label, self[package_absolute_label].source_dir, self[package_absolute_label].source_file))
            #assert False
        self[package_absolute_label] = package

    def remove_package(self, package):
        package_absolute_label = package.absolute_label
        del self[package_absolute_label]

