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

__all__ = ['Version',
]

import re

class Version(str):
    RE_SPLIT = re.compile(r"[\.\-_]")
    def __init__(self, init):
        super().__init__(init)
        self._tokens = []
        for token in self.RE_SPLIT.split(self):
            try:
                token = int(token)
            except ValueError:
                pass
            self._tokens.append(token)
        
    def comparable(self, token_a, token_b):
        if isinstance(token_a, str):
            if not isinstance(token_b, str):
                token_b = str(token_b)
        elif isinstance(token_b, str):
            if not isinstance(token_a, str):
                token_a = str(token_a)
        return token_a, token_b

    def __COMPARE(self, other, t_compare, l_compare):
        if not isinstance(other, Version):
            other = Version(other)
        s_tokens = self._tokens
        o_tokens = other._tokens
        for s_token, o_token in zip(s_tokens, o_tokens):
            s_token, o_token = self.comparable(s_token, o_token)
            if t_compare(s_token, o_token):
                return True
            elif t_compare(o_token, s_token):
                return False
        return l_compare(len(s_tokens), len(o_tokens))

    @staticmethod
    def __LT(x, y):
        return x < y

    @staticmethod
    def __LE(x, y):
        return x <= y

    @staticmethod
    def __GT(x, y):
        return x > y

    @staticmethod
    def __GE(x, y):
        return x >= y

    def __lt__(self, other):
        return self.__COMPARE(other, self.__LT, self.__LT)

    def __le__(self, other):
        return self.__COMPARE(other, self.__LT, self.__LE)

    def __gt__(self, other):
        return self.__COMPARE(other, self.__GT, self.__GT)

    def __ge__(self, other):
        return self.__COMPARE(other, self.__GT, self.__GE)

if __name__ == "__main__":
    vas = input("a version: ")
    va = Version(vas)
    while True:
        vbs = input("b version: ")
        if vbs == '':
            break
        vb = Version(vbs)
        print("{0} <  {1} ? {2}".format(va, vb, va <  vb))
        print("{0} <= {1} ? {2}".format(va, vb, va <= vb))
        print("{0} >  {1} ? {2}".format(va, vb, va >  vb))
        print("{0} >= {1} ? {2}".format(va, vb, va >= vb))

