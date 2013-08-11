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

from .transition import *
from .registry import Registry

import abc

__all__ = ['Component']

class Component(object):
    REGISTRY = Registry()
    def __init__(self):
        self._transitions = []
        self.register()

    def register(self):
        self.__class__.REGISTRY.register(self)

    def add_transition(self, transition):
        assert isinstance(transition, Transition)
        self._transitions.append(transition)
        
    def setenv(self, var_name, var_value):
        self.add_transition(SetEnv(var_name, var_value))

    def prepend_path(self, var_name, var_value, separator=None):
        self.add_transition(PrependPath(var_name, var_value, separator))

    def append_path(self, var_name, var_value, separator=None):
        self.add_transition(AppendPath(var_name, var_value, separator))

    def apply(self, session):
        for transition in self._transitions:
            transition.apply(session)

