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

import argparse
import collections

from .autocompletedict import AutoCompleteDict

class _AutoCompleteOrderedDict(AutoCompleteDict, collections.OrderedDict):
    pass

def autocomplete_monkey_patch(parser):
    #print(parser)
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            action._name_parser_map = _AutoCompleteOrderedDict(action._name_parser_map)
            action.choices = _AutoCompleteOrderedDict(action.choices)
            for subparser in action.choices.values():
                autocomplete_monkey_patch(subparser)

