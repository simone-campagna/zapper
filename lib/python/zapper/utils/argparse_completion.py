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

COMPLETION_VERSION = "1.1"

class CompletionGenerator(object):
    RE_INVALID = re.compile(r"[^\w]")
    def __init__(self,
                    parser,
                    name=None,
                    output_stream=None,
                    skip_keys=None,
                    complete_function_name=None,
                    complete_add_arguments_name=None,
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
        if complete_add_arguments_name is None:
            complete_add_arguments_name = 'complete_add_arguments'
        self.complete_add_arguments_name = complete_add_arguments_name
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
ZAPPER_CURRENT_COMPLETION_VERSION={}
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
            complete_add_arguments = parser.get_default(self.complete_add_arguments_name)
            if complete_add_arguments:
                add_arguments = ' '.join(complete_add_arguments)
            else:
                add_arguments = ''
            complete_function_code = 'current_keys="$current_keys $({activate_complete_function} {current_stack} {add_arguments})"'.format(
                activate_complete_function = self.activate_complete_function,
                current_keys = current_keys,
                current_stack = current_stack,
                add_arguments = add_arguments,
            )
            #input(complete_function_code)
        current_command = stack[-1]
        current_level = len(stack)
        format_d = dict(
            function_name=function_name,
            current_level=current_level,
            previous_level=current_level - 1,
            current_keys=current_keys, 
            current_stack=current_stack, 
            current_command=current_command, 
            complete_function_code=complete_function_code,
        )
        subcommands = [key for key in keys if not key.startswith('-')]
        self.output_stream.write("""
{function_name} ()
{{
    local index
    local cur
    local current_keys
    cur=${{COMP_WORDS[$COMP_CWORD]}}
    COMPREPLY=()
""".format(**format_d))
        if subcommands:
            self.output_stream.write("""
    # search current index
    local index={previous_level}
    while [[ $index -lt ${{#COMP_WORDS[*]}} ]] ; do
        case "${{COMP_WORDS[$index]}}" in
            {current_command})
                break
                ;;
        esac
        index=$(( $index + 1 ))
    done
    # search next function
    while [[ $index -lt $(( ${{#COMP_WORDS[*]}} - 1 )) ]] ; do
            case "${{COMP_WORDS[$index]}}" in
""".format(**format_d))

            for subcommand in subcommands:
                subcommand_function = self.get_function_name(stack + [subcommand])
                if not subcommand_function in self._generated_functions:
                    continue
                self.output_stream.write("""\
                {subcommand})
                    {subcommand_function} 
                    return $?
                    ;;
""".format(subcommand=subcommand, subcommand_function=subcommand_function))
            self.output_stream.write("""
            esac
            index=$(( $index + 1 ))
    done
""")

        self.output_stream.write("""
    current_keys='{current_keys}'
    {complete_function_code}
    COMPREPLY=( $( compgen -W '$current_keys' -- $cur) )
    return 0
}}
""".format(**format_d))
    #echo "<<<{function_name} -> {current_keys}>>>"
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
            elif hasattr(action, 'choices') and action.choices:
                for key in action.choices:
                    if self._key_to_skip(key):
                        continue
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
        complete_add_arguments_name=None,
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
                complete_add_arguments_name=complete_add_arguments_name,
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
            complete_add_arguments_name=complete_add_arguments_name,
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
