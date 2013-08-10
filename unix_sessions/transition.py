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

__all__ = ['Transition',
           'SetEnvironmentVariable',
           'PrependEnvironmentVariable',
           'AppendEnvironmentVariable',
]

import abc

class Transition(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def apply(self, session):
        pass

class EnvironmentTransition(Transition):
    def __init__(self, var_name, var_value, separator=':'):
        self.var_name = var_name
        self.var_value = var_value
        self.separator = separator

class SetEnvironmentVariable(EnvironmentTransition):
    def apply(self, session):
        session.environment.set_var(self.var_name, self.var_value, self.separator)
        
class PrependEnvironmentVariable(EnvironmentTransition):
    def apply(self, session):
        session.environment.prepend_var(self.var_name, self.var_value, self.separator)
        
class AppendEnvironmentVariable(EnvironmentTransition):
    def apply(self, session):
        session.environment.append_var(self.var_name, self.var_value, self.separator)
        
