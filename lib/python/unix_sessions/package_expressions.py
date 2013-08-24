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
import collections

from .expression import Expression, AttributeGetter, InstanceGetter, MethodCaller, ConstExpression

__all__ = ['Package',
           'NAME',
           'FULL_NAME',
           'LABEL',
           'FULL_LABEL',
           'VERSION',
           'CATEGORY',
           'PACKAGE',
           'HAS_TAG',
           'ALL_EXPRESSIONS']

NAME = AttributeGetter('name', 'NAME')
FULL_NAME = AttributeGetter('full_name', 'FULL_NAME')
LABEL = AttributeGetter('label', 'LABEL')
FULL_LABEL = AttributeGetter('full_label', 'FULL_LABEL')
VERSION = AttributeGetter('version', 'VERSION')
CATEGORY = AttributeGetter('category', 'CATEGORY')
PACKAGE = InstanceGetter('PACKAGE')

def HAS_TAG(tag):
    return MethodCaller('has_tag', method_p_args=(tag, ), symbol='HAS_TAG({0!r})'.format(tag))

ALL_EXPRESSIONS = {
    'NAME': NAME,
    'FULL_NAME': FULL_NAME,
    'LABEL': LABEL,
    'FULL_LABEL': FULL_LABEL,
    'VERSION': VERSION,
    'CATEGORY': CATEGORY,
    'PACKAGE': PACKAGE,
    'HAS_TAG': HAS_TAG,
}

