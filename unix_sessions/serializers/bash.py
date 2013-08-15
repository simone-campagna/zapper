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

import sys
import abc
import collections
from ..serializer import Serializer

class bash(Serializer):
    def serialize_var_set(self, stream, var_name, var_value):
        stream.write("export {0}={1!r}\n".format(var_name, var_value))

    def serialize_var_unset(self, stream, var_name):
        stream.write("export -n {0}\nunset {0}\n".format(var_name))
        
    def serialize_remove_filename(self, stream, filename):
        stream.write("rm -f {0}\n".format(filename))

    def serialize_init(self, stream):
        stream.write("""\
function uxs {{
    typeset _filename="$TMPDIR/$$.$RANDOM"
    eval $(env UXS_CURRENT_SESSION="{shell}:${{_filename}}" ./sessions "$@")
}}\n""".format(
        shell=self.__registry_name__,
        ))
