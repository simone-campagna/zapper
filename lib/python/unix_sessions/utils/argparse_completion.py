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
import re
import sys
import argparse

COMPLETION_VERSION = 1.0

class CompletionGenerator(object):
    RE_INVALID = re.compile(r"[^\w]")
    def __init__(self,
                    parser,
                    name=None,
                    output_stream=None,
                    skip_keys=None,
                    complete_function_name=None,
                    activate_complete_function=None,
                    progname=None):
        self.parser = parser
        if name is None:
            name = os.path.basename(sys.argv[0])
        self.name = self._convert(name)
        if output_stream is None:
            output_stream = sys.stdout
        if skip_keys is None:
            skip_keys = []
        self._skip_keys = []
        for skip_re in skip_keys:
            if isinstance(skip_re, str):
                skip_re = re.compile(skip_re)
            self._skip_keys.append(skip_re)
        self.output_stream = output_stream
        if complete_function_name is None:
            complete_function_name = 'complete_function'
        self.complete_function_name = complete_function_name
        if activate_complete_function is None:
            activate_complete_function = ''
        self.activate_complete_function = activate_complete_function
        if progname is None:
            progname = sys.argv[0]
        self.progname = progname
        self._generated_functions = set()
        self.complete(self.parser, [self.name])
        function = self.get_function_name([self.name])
        self.output_stream.write("""\
complete -F {function} -o filenames {name}
""".format(function=function, name=name))

    @classmethod
    def write_version_file(cls, stream):
        stream.write("""\
UXS_CURRENT_COMPLETION_VERSION={}
""".format(COMPLETION_VERSION))

    def _convert(self, key):
        return self.RE_INVALID.sub('X', key)

    def get_function_name(self, stack):
        return '_' + '_'.join(self._convert(key) for key in stack)

    def generate_function(self, parser, stack, keys):
        #print(">>> {} : {}".format('.'.join(stack), keys))
        function_name = self.get_function_name(stack)
        current_keys = ' '.join(keys)
        current_stack = ' '.join(stack)
        complete_function_code = ''
        complete_function = parser.get_default(self.complete_function_name)
        if complete_function:
            complete_function_code = 'current_keys="$current_keys $({activate_complete_function} {current_stack})"'.format(
                activate_complete_function = self.activate_complete_function,
                current_keys = current_keys,
                current_stack = current_stack,
            )
            input(complete_function_code)
        format_d = dict(
            function_name=function_name,
            level=len(stack),
            current_keys=current_keys, 
            current_stack=current_stack, 
            complete_function_code=complete_function_code,
        )
        self.output_stream.write("""
{function_name} ()
{{
  local index
  index={level}
  local cur
  local current_keys
  cur=${{COMP_WORDS[$index]}}
  COMPREPLY=()
  if [[ $COMP_CWORD -gt $index ]] ; then
    case "${{COMP_WORDS[$index]}}" in
""".format(**format_d))

        for key in keys:
            key_function = self.get_function_name(stack + [key])
            if not key_function in self._generated_functions:
                continue
            self.output_stream.write("""\
      {key})
        {key_function}
        ;;
""".format(key=key, key_function=self.get_function_name(stack + [key])))

        self.output_stream.write("""
    esac
  else
    current_keys='{current_keys}'
    {complete_function_code}
    COMPREPLY=( $( compgen -W '$current_keys' -- $cur) )
  fi
  return 0
}}
""".format(**format_d))
        self._generated_functions.add(function_name)
    
    def _key_to_skip(self, key):
        for skip_re in self._skip_keys:
            if skip_re.match(key):
                return True
        else:
            return False
    
    def _sort_key_function(self, key):
        return key

    def complete(self, parser, stack):
        keys = []
        label = '.'.join(stack)
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                #print("{}:subparser: choices={}".format(label, action.choices))
                for key, subparser in action.choices.items():
                    if self._key_to_skip(key):
                        continue
                    self.complete(subparser, stack + [key])
                    keys.append(key)
            else:
                #print("{}:action: {}".format(label, action.option_strings))
                keys.extend(key for key in action.option_strings if not self._key_to_skip(key))
        #keys.sort(key=self._sort_key_function)
        self.generate_function(parser, stack, keys)

def complete(
        parser,
        filename=None,
        version_filename=None,
        skip_keys=None,
        complete_function_name=None,
        activate_complete_function=None,
        progname=None,
        ):
    if isinstance(filename, str):
        with open(filename, "w") as f_out:
            CompletionGenerator(
                parser,
                output_stream=f_out,
                skip_keys=skip_keys,
                complete_function_name=complete_function_name,
                activate_complete_function=activate_complete_function,
                progname=progname)
    else:
        stream = filename
        filename = getattr(stream, 'name', None)
        CompletionGenerator(
            parser,
            output_stream=stream,
            skip_keys=skip_keys,
            complete_function_name=complete_function_name,
            activate_complete_function=activate_complete_function,
            progname=progname)
    
    if version_filename is None:
        default_version_filename = filename + '.version'
        version_filename = default_version_filename

    if version_filename:
        if isinstance(version_filename, str):
            with open(version_filename, "w") as f_out:
                CompletionGenerator.write_version_file(f_out)
        else:
            CompletionGenerator.write_version_file(f_out)
