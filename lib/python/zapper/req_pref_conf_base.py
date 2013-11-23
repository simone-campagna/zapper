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

__all__ = ['Product']

import re
import abc

from .expression import Expression, ConstExpression

class ReqPrefConfBase(metaclass=abc.ABCMeta):
    def __init__(self, *p_args, **n_args):
        self._requirements = []
        self._preferences = []
        self._conflicts = []

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
            if isinstance(e, ReqPrefConfBase):
                expression = self.make_self_expression()
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

