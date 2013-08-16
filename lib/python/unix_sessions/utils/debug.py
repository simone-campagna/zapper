#!/usr/bin/env python

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

import logging
import sys
import os

from . import trace

DEBUG = False
VERBOSE = False

def _create_logger(name, level=logging.WARNING):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger

LOGGER = _create_logger('UXS')

def set_verbose(enable):
    global VERBOSE, LOGGER
    VERBOSE = enable
    set_logger_level()

def set_debug(enable):
    global DEBUG, LOGGER
    DEBUG = enable
    set_logger_level()
    if enable:
        trace.set_trace(True)

def set_logger_level():
    if DEBUG:
        LOGGER.setLevel(logging.DEBUG)
    elif VERBOSE:
        LOGGER.setLevel(logging.INFO)
    else:
        LOGGER.setLevel(logging.WARNING)

