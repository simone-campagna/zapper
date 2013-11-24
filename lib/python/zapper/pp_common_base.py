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

__all__ = ['PPCommonBase']

import re
import abc

from .transition import *
from .parameters import PARAMETERS
from .expression import Expression, ConstExpression
from .utils.debug import LOGGER

class PPCommonBase(Transition):
    def __init__(self, *p_args, **n_args):
        self._source_dir = PARAMETERS.current_dir
        self._source_file = PARAMETERS.current_file
        self._source_module = PARAMETERS.current_module
        self._requirements = []
        self._preferences = []
        self._conflicts = []
        self._transitions = []

    @property
    def source_dir(self):
        return self._source_dir

    @property
    def source_file(self):
        return self._source_file

    @property
    def source_module(self):
        return self._source_module


    def get_requirements(self):
        for requirement in self._requirements:
            yield requirement

    def get_preferences(self):
        for preference in self._preferences:
            yield preference

    def get_conflicts(self):
        for conflict in self._conflicts:
            yield conflict

    def requires(self, expression, *expressions):
        self._requirements.append(self._create_expression(expression, *expressions))

    def prefers(self, expression, *expressions):
        self._preferences.append(self._create_expression(expression, *expressions))

    def conflicts(self, expression, *expressions):
        self._conflicts.append(self._create_expression(expression, *expressions))

    def match_requirements(self, packages):
        return self.match_expressions(packages, tuple(self.get_requirements()))

    def match_preferences(self, packages):
        return self.match_expressions(packages, tuple(self.get_preferences()))

    def match_conflicts(self, packages):
        conflicts = self._match_conflicts(packages)
        for package in packages:
            conflicts.extend(package._match_conflicts([self]))
        return conflicts

    def _match_conflicts(self, loaded_packages):
        conflicts = []
        for expression in self.get_conflicts():
            for loaded_package in loaded_packages:
                if loaded_package is self:
                    # a package cannot conflicts with itself
                    continue
                expression.bind(loaded_package)
                if expression.get_value():
                    conflicts.append((self, expression, loaded_package))
        return conflicts

    @abc.abstractmethod
    def make_self_expression(self):
        pass

    def _create_expression(self, *expressions):
        result = None
        for e in expressions:
            if isinstance(e, PPCommonBase):
                expression = e.make_self_expression()
            elif isinstance(e, str):
                expression = NAME == e
            elif isinstance(e, Expression):
                expression = e
            else:
                expression = ConstExpression(e)
            if result is None:
                result = expression
            else:
                result = result & expression
        return result

    def get_transitions(self):
        for transition in self._transitions:
            yield transition

    def add_transition(self, transition):
        assert isinstance(transition, Transition)
        self._transitions.append(transition)

    def var_set(self, var_name, var_value):
        self.add_transition(SetEnv(var_name, var_value))

    def var_unset(self, var_name):
        self.add_transition(UnsetEnv(var_name))

    def list_prepend(self, var_name, var_value, separator=None):
        self.add_transition(PrependList(var_name, var_value, separator))

    def path_prepend(self, var_name, var_value, separator=None):
        self.add_transition(PrependPath(var_name, var_value, separator))

    def list_append(self, var_name, var_value, separator=None):
        self.add_transition(AppendList(var_name, var_value, separator))

    def path_append(self, var_name, var_value, separator=None):
        self.add_transition(AppendPath(var_name, var_value, separator))

    def list_remove(self, var_name, var_value, separator=None):
        self.add_transition(RemoveList(var_name, var_value, separator))

    def path_remove(self, var_name, var_value, separator=None):
        self.add_transition(RemovePath(var_name, var_value, separator))

    def apply(self, session):
        LOGGER.debug("{0}[{1}]: applying...".format(self.__class__.__name__, self))
        for transition in self.get_transitions():
            transition.apply(session)

    def revert(self, session):
        LOGGER.debug("{0}[{1}]: reverting...".format(self.__class__.__name__, self))
        for transition in self.get_transitions():
            transition.revert(session)


