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



def plural(s, number):
    if number == 1:
        return s
    else:
        s = s.strip()
        if s[-1] == 'y':
            p = s[:-1] + 'ies'
        else:
            p = s + 's'
    return p

def plural_string(s, number):
    return "#{0} {1}".format(number, plural(s, number))

def string_to_bool(s):
    try:
        i = int(s)
        return bool(i)
    except ValueError as e:
        pass
    if s.lower() in {'true', 'on'}:
        return True
    elif s.lower() in {'false', 'off'}:
        return False
    else:
        raise ValueError("invalid value {0!r} for bool".format(s))

def bool_to_string(b):
    return str(bool(b))
