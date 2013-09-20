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

import random
import os

class RandomNameSequence(object):
    def __init__(self, width=8, characters=None, seed=None):
        if characters is None:
            characters = "abcdefghijklmnopqrstuvwxyz0123456789_"
        self.width = width
        self.characters = characters
        self.random = random.Random(seed)
 
    def __iter__(self):
        choice = self.random.choice
        characters = self.characters
        yield ''.join(choice(characters) for i in range(self.width))
        
