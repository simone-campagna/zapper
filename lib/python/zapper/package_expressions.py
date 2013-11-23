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
           'ABSOLUTE_NAME',
           'LABEL',
           'ABSOLUTE_LABEL',
           'VERSION',
           'CATEGORY',
           'PACKAGE',
           'PRODUCT',
           'HAS_TAG',
           'ALL_EXPRESSIONS']

NAME = AttributeGetter('name', 'NAME')
ABSOLUTE_NAME = AttributeGetter('absolute_name', 'ABSOLUTE_NAME')
LABEL = AttributeGetter('label', 'LABEL')
ABSOLUTE_LABEL = AttributeGetter('absolute_label', 'ABSOLUTE_LABEL')
VERSION = AttributeGetter('version', 'VERSION')
CATEGORY = AttributeGetter('category', 'CATEGORY')
PACKAGE = InstanceGetter('PACKAGE')
PRODUCT = AttributeGetter('product', 'PRODUCT')

def HAS_TAG(tag):
    return MethodCaller('has_tag', method_p_args=(tag, ), symbol='HAS_TAG({0!r})'.format(tag))

ALL_EXPRESSIONS = {
    'NAME': NAME,
    'ABSOLUTE_NAME': ABSOLUTE_NAME,
    'LABEL': LABEL,
    'ABSOLUTE_LABEL': ABSOLUTE_LABEL,
    'VERSION': VERSION,
    'CATEGORY': CATEGORY,
    'PACKAGE': PACKAGE,
    'PRODUCT': PRODUCT,
    'HAS_TAG': HAS_TAG,
}

