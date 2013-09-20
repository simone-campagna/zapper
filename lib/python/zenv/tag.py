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

class Tag(str):
    __tags__ = set()
    def __new__(cls, value):
        if not value in cls.__tags__:
            cls.add_tag(value)
        return super().__new__(cls, value)

    @classmethod
    def add_tag(cls, tag):
        if not tag in cls.__tags__:
            cls.__tags__.add(tag)

