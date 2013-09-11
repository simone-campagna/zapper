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

class AutoCompleteDict(dict):
    def _find_match(self, key):
        contains = super().__contains__
        if not contains(key):
            if isinstance(key, str):
                matching_key = None
                use_key = None
                for dict_key in self:
                    if isinstance(dict_key, str) and dict_key.startswith(key):
                        if matching_key is None:
                            matching_key = dict_key
                        else:
                            break
                else:
                    use_key = matching_key
                if use_key is not None:
                    key = use_key
        return key

    def __getitem__(self, key):
        return super().__getitem__(self._find_match(key))

    def __contains__(self, key):
        return super().__contains__(self._find_match(key))

if __name__ == "__main__":

    d = AutoCompleteDict()
    for key in 'alfa', 'beta', 'alpha', 'babar':
        d[key] = key.upper()

    for key in 'a', 'al', 'alp', 'alf', 'b', 'be', 'baba', 'alfa', 'alfar':
        try:
            value = d[key]
        except Exception as e:
            #import traceback
            #traceback.print_exc()
            value = repr(e)
        print("d[{!r}] = {} [{}]".format(key, value, key in d))
        #print("{!r} in d -> {}".format(key, key in d))

