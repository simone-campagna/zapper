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

from .parameters import PARAMETERS

class SourceBase(object):
    def __init__(self, *p_args, **n_args):
        self._source_dir = PARAMETERS.current_dir
        self._source_file = PARAMETERS.current_file
        self._source_module = PARAMETERS.current_module

    @property
    def source_dir(self):
        return self._source_dir

    @property
    def source_file(self):
        return self._source_file

    @property
    def source_module(self):
        return self._source_module


