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

import os

ZAPPER_HOME_DIR = None
ZAPPER_ADMIN_USER = None
ZAPPER_VERSION = None

def set_home_dir(home_dir):
    global ZAPPER_HOME_DIR
    ZAPPER_HOME_DIR = home_dir

def get_home_dir():
    return ZAPPER_HOME_DIR

def set_admin_user(admin_user):
    global ZAPPER_ADMIN_USER
    ZAPPER_ADMIN_USER = admin_user

def get_admin_user():
    return ZAPPER_ADMIN_USER

def set_version(version):
    global ZAPPER_VERSION
    ZAPPER_VERSION = version

def get_version():
    return ZAPPER_VERSION

def get_zapper_profile(shell_name="$SHELL"):
    return os.path.join(ZAPPER_HOME_DIR, 'etc', 'profile.d', 'zapper.{}'.format(shell_name))
    
