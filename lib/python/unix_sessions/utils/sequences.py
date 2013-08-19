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

def unique(sequence):
    seen = set()
    for item in sequence:
        if not item in seen:
            yield item
            seen.add(item)

def difference(sequence0, sequence1):
    seen = set()
    if isinstance(sequence1, (set, frozenset)):
        set1 = sequence1
    else:
        set1 = set(sequence1)
    for item in sequence0:
        if not item in set1:
            yield item
            seen.add(item)

if __name__ == "__main__":
    import sys
    l = sys.argv[1:]
    print("orig:   ", l)
    print("unique: ", list(unique(l)))
    print("orig:   ", l)
    
