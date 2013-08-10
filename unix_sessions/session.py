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

from .environment import Environment
from .component import Component

class Session(object):
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self._environment = Environment()

    @property
    def environment(self):
        return self._environment


    def __repr__(self):
        return "{c}(name={n!r}, type={t!r})".format(c=self.__class__.__name__, n=self.name, t=self.type)
    __str__ = __repr__
    

