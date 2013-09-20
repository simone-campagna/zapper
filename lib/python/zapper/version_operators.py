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

import abc

class MetaVersionOperator(abc.ABCMeta):
    __operators__ = {}
    def __new__(mcls, class_name, class_bases, class_dict):
        cls = super().__new__(mcls, class_name, class_bases, class_dict)
        symbol = cls.__symbol__
        if symbol is not None:
            assert not symbol in mcls.__operators__
            mcls.__operators__[symbol] = cls
        return cls

        
class VersionOperator(metaclass=MetaVersionOperator):
    __symbol__ = None
    def __init__(self, version):
        self.version = version

    @abc.abstractmethod
    def __call__(self, version):
        pass

class TrueOperatorVersion(VersionOperator):
    def __call__(self, version):
        return True

class FalseOperatorVersion(VersionOperator):
    def __call__(self, version):
        return False

class EqVersionOperator(VersionOperator):
    __symbol__ = "=="
    def __call__(self, version):
        return version == self.version

class NeVersionOperator(VersionOperator):
    __symbol__ = "!="
    def __call__(self, version):
        return version != self.version

class LtVersionOperator(VersionOperator):
    __symbol__ = "<"
    def __call__(self, version):
        return version <  self.version

class LeVersionOperator(VersionOperator):
    __symbol__ = "<="
    def __call__(self, version):
        return version <= self.version

class GtVersionOperator(VersionOperator):
    __symbol__ = ">"
    def __call__(self, version):
        return version >  self.version

class GeVersionOperator(VersionOperator):
    __symbol__ = ">="
    def __call__(self, version):
        return version >= self.version

def get_version_operator(version):
    if version is None:
        operator_class = TrueOperatorVersion
    else:
        for symbol, operator_class in VersionOperator.__operators__.items():
            if version.startswith(symbol):
                version = version[len(symbol):]
                break
        else:
            symbol = '=='
        operator_class = VersionOperator.__operators__[symbol]
    return operator_class(version)
