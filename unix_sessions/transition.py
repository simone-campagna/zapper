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
           'SetEnv',
           'UnsetEnv',
           'PrependPath',
           'AppendPath',
           'RemovePath',
]

import abc

class Transition(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def apply(self, session):
        """apply(session) -> apply the transition onto the session"""
        pass

    @abc.abstractmethod
    def revert(self, session):
        """revert(session) -> revert the transition on the session"""
        pass

class EnvVarTransition(Transition):
    def __init__(self, var_name):
        self.var_name = var_name

    def _cache_var_name(self):
        return "_UXS_CACHE_{0}_".format(self.var_name)

class EnvVarValueTransition(EnvVarTransition):
    def __init__(self, var_name, var_value):
        super().__init__(var_name)
        self.var_value = str(var_value)

class EnvListTransition(EnvVarValueTransition):
    def __init__(self, var_name, var_value, separator=None):
        super().__init__(var_name, var_value)
        if separator is None:
            separator = ':'
        self.separator = separator

class SetEnv(EnvVarValueTransition):
    def apply(self, session):
        session.environment.var_set(self.var_name, self.var_value)
        
    def revert(self, session):
        session.environment.var_unset(self.var_name)

class UnsetEnv(EnvVarTransition):
    def apply(self, session):
        cache_var_value = session.environment.var_get(self.var_name)
        print("AAA", self.var_name, cache_var_value)
        if cache_var_value is not None:
            cache_var_name = self._cache_var_name()
            session.environment.var_set(cache_var_name, cache_var_value)
            session.environment.var_unset(self.var_name)
        
    def revert(self, session):
        cache_var_name = self._cache_var_name()
        cache_var_value = session.environment.var_get(cache_var_name)
        if cache_var_value is not None:
            session.environment.var_set(self.var_name, cache_var_value)
            session.environment.var_unset(cache_var_name)

class PrependList(EnvListTransition):
    def apply(self, session):
        session.environment.list_prepend(self.var_name, self.var_value, self.separator)
        
    def revert(self, session):
        session.environment.list_remove(self.var_name, self.var_value, self.separator)

class PrependPath(EnvListTransition):
    def apply(self, session):
        session.environment.path_prepend(self.var_name, self.var_value, self.separator)
        
    def revert(self, session):
        session.environment.path_remove(self.var_name, self.var_value, self.separator)

class AppendList(EnvListTransition):
    def apply(self, session):
        session.environment.list_append(self.var_name, self.var_value, self.separator)
        
    def revert(self, session):
        session.environment.list_remove(self.var_name, self.var_value, self.separator)

class AppendPath(EnvListTransition):
    def apply(self, session):
        session.environment.path_append(self.var_name, self.var_value, self.separator)
        
    def revert(self, session):
        session.environment.path_remove(self.var_name, self.var_value, self.separator)

class RemoveList(EnvListTransition):
    def apply(self, session):
        cache_var_name = self._cache_var_name()
        cache_var_value = session.environment.var_get(self.var_name)
        session.environment.var_set(cache_var_name, cache_var_value)
        session.environment.list_remove(self.var_name, self.var_value, self.separator)
        
    def revert(self, session):
        cache_var_name = self._cache_var_name()
        cache_var_value = session.environment.var_get(cache_var_name)
        session.environment.list_insert(self.var_name, self.var_value, cache_var_value, self.separator)
        session.environment.var_unset(cache_var_name)

class RemovePath(EnvListTransition):
    def apply(self, session):
        cache_var_name = self._cache_var_name()
        cache_var_value = session.environment.var_get(self.var_name)
        session.environment.var_set(cache_var_name, cache_var_value)
        session.environment.path_remove(self.var_name, self.var_value, self.separator)
        
    def revert(self, session):
        cache_var_name = self._cache_var_name()
        cache_var_value = session.environment.var_get(cache_var_name)
        session.environment.path_insert(self.var_name, self.var_value, cache_var_value, self.separator)
        session.environment.var_unset(cache_var_name)

