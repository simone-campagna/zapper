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

from .config import Config

COMMON_CONFIG = {
    'quiet': '',
    'verbose': '',
    'debug': '',
    'trace': '',
    'subpackages': '',
    'directories': '',
    'available_package_format': '',
    'available_session_format': '',
    'loaded_package_format': '',
    'package_dir_format': '',
    'package_sort_keys': '',
    'package_dir_sort_keys': '',
    'session_sort_keys': '',
    'resolution_level': '',
    'enable_default_version': '',
    'enable_relative_packages': '',
    'show_header': '',
    'show_header_if_empty': '',
    'show_translation': '',
    'filter_packages': '',
}

USER_HOST_CONFIG = COMMON_CONFIG.copy()
USER_HOST_CONFIG['restricted_keys'] = ''
USER_HOST_CONFIG['default_session'] = ''
USER_HOST_CONFIG['default_packages'] = ''
USER_HOST_CONFIG['persistent_sessions_dir'] = ''
USER_HOST_CONFIG['temporary_sessions_dir'] = ''

VERSION_DEFAULTS = {
}

GENERAL = {
    'categories': '',
}
