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

class Category(str):
    __categories__ = ['suite']
    def __init__(self, value):
        if not value in self.__categories__:
            raise KeyError("invalid category {0!r}".format(value))
        super().__init__(value)

    @classmethod
    def categories(cls):
        return iter(cls.__categories__)

    @classmethod
    def add_category(cls, *categories):
        for category in categories:
            if not category in cls.__categories__:
                cls.__categories__.append(category)
