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
import sys
import argparse
import collections

from .helper import Helper
from ..manager import Manager
from ..errors import SessionConfigError
from ..utils.debug import set_quiet, set_verbose, set_debug, LOGGER
from ..utils.trace import set_trace, trace
from ..utils.install_data import set_home_dir, set_admin_user, set_version, get_version, get_zapper_profile
from ..utils.argparse_autocomplete import autocomplete_monkey_patch
from ..utils.strings import string_to_bool

_ZAPPER_COMPLETE_FUNCTION = string_to_bool(os.environ.get("ZAPPER_COMPLETE_FUNCTION", "False"))
_ZAPPER_QUIET_MODE = string_to_bool(os.environ.get("ZAPPER_QUIET_MODE", "False"))

def _set_global_flags(enable_complete_function, *, quiet, verbose, debug, trace):
    if enable_complete_function:
        # to avoid unwanted log output during completion
        set_quiet()
        #set_trace(False)
        #set_verbose(False)
        #set_debug(False)
    else:
        if quiet:
            set_quiet()
        else:
            set_verbose(verbose)
            set_debug(debug)
        set_trace(trace)

def create_manager():
    try:
        manager = Manager()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        trace(True)
        LOGGER.critical("{0}: {1}".format(exc_type.__name__, exc_value))
        if not isinstance(exc_value, SessionConfigError):
            LOGGER.critical("Unrecoverable error\n")
        sys.exit(1)

    _set_global_flags(
        _ZAPPER_COMPLETE_FUNCTION or _ZAPPER_QUIET_MODE,
        quiet=manager.get_config_key('quiet'),
        verbose=manager.get_config_key('verbose'),
        debug=manager.get_config_key('debug'),
        trace=manager.get_config_key('trace'),
    )

    try:
        manager.restore_session()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        trace(True)
        LOGGER.critical("{0}: {1}".format(exc_type.__name__, exc_value))
        if not isinstance(exc_value, SessionConfigError):
            LOGGER.critical("Session is corrupted. Unset environment variable ZAPPER_SESSION and try again with a new session.")
        sys.exit(1)

    if manager.translation_name is None:
        LOGGER.critical("Translation is not defined. Zapper environment is not complete. Try sourcing {!r}".format(get_zapper_profile()))
        sys.exit(2)
    return manager

def create_top_level_parser(manager):
    class Formatter(argparse.RawTextHelpFormatter):
        def __init__(self, prog, indent_increment=2, max_help_position=27, width=None):
            super().__init__(prog, indent_increment, max_help_position, width)

    #enable_completion_option = manager.translation_name == 'bash'
    enable_completion_option = manager.translation_name == 'bash' and os.environ.get("ZAPPER_ENABLE_BASH_COMPLETION_OPTION", "").title() == "True"

    helper = Helper(manager)

    admin_mode = manager.is_admin()

    package_options = collections.OrderedDict()
    package_options['version_defaults'] = ('versions', [])

    #Formatter = argparse.HelpFormatter

    ### Common parser
    common_parser = argparse.ArgumentParser(
        add_help=False,
        formatter_class=Formatter)

    common_parser.add_argument("--version", "-V",
        action="version",
        version=get_version(),
        help="show zapper version")

    common_parser.add_argument("--verbose", "-v",
        action="store_true",
        default=manager.get_config_key('verbose'),
        help="set verbose on")

    common_parser.add_argument("--debug", "-d",
        action="store_true",
        default=manager.get_config_key('debug'),
        help="set debug on")

    common_parser.add_argument("--quiet", "-q",
        action="store_true",
        default=manager.get_config_key('quiet'),
        help="quiet mode")

    common_parser.add_argument("--trace", "-t",
        action="store_true",
        default=manager.get_config_key('trace'),
        help="show traceback on errors")

    common_parser.add_argument("--dry-run", "-D",
        dest="dry_run",
        action="store_true",
        default=False,
        help="do not apply changes")

    common_parser.add_argument("--force", "-f",
        dest="force",
        action="store_true",
        default=False,
        help="allow changes to read-only sessions")

    common_parser.add_argument("--show-header",
        dest='show_header',
        action="store_true",
        default=manager.get_config_key('show_header'),
        help="show header for non-empty tables")

    common_parser.add_argument("--hide-header",
        dest='show_header',
        action="store_false",
        default=manager.get_config_key('show_header'),
        help="do not show header for non-empty tables")

    common_parser.add_argument("--show-header-if-empty",
        dest='show_header_if_empty',
        action="store_true",
        default=manager.get_config_key('show_header_if_empty'),
        help="show header for empty tables")

    common_parser.add_argument("--hide-header-if-empty",
        dest='show_header_if_empty',
        action="store_false",
        default=manager.get_config_key('show_header_if_empty'),
        help="show header for empty tables")

    common_parser.add_argument("--show-translation",
        dest='show_translation',
        action="store_true",
        default=manager.get_config_key('show_translation'),
        help="show translation")

    package_format_parser = argparse.ArgumentParser(
        add_help=False,
        formatter_class=Formatter)

    package_format_parser.add_argument("--package-format",
        type=manager.PackageFormat,
        default=None,
        help="set the format for package info")

    package_format_parser.add_argument("--package-sort-keys",
        type=manager.PackageSortKeys,
        default=None,
        help="set the sorting keys for packages")

    package_dir_format_parser = argparse.ArgumentParser(
        add_help=False,
        formatter_class=Formatter)

    package_dir_format_parser.add_argument("--package-dir-format",
        type=manager.PackageDirFormat,
        default=None,
        help="set the format for package dir info")

    package_dir_format_parser.add_argument("--package-dir-sort-keys",
        type=manager.PackageDirSortKeys,
        default=None,
        help="set the sorting keys for package directories")

    session_format_parser = argparse.ArgumentParser(
        add_help=False,
        formatter_class=Formatter)

    session_format_parser.add_argument("--session-format",
        type=manager.SessionFormat,
        default=None,
        help="set the format for session info")

    session_format_parser.add_argument("--session-sort-keys",
        type=manager.SessionSortKeys,
        default=None,
        help="set the sorting keys for sessions")

    ### Top-level parser
    top_level_parser = argparse.ArgumentParser(
        parents = [common_parser],
        formatter_class=Formatter,
        description="""\
Change the current session""",
        epilog = "")

    top_level_parser.set_defaults(
        package_format=None,
        package_sort_keys=None,
        package_dir_format=None,
        package_dir_sort_keys=None,
        session_format=None,
        session_sort_keys=None,
    )

    ### Subparsers
    top_level_subparsers = top_level_parser.add_subparsers(
        description="Commands to change the current session.")

    ### Help 
    parser_help = top_level_subparsers.add_parser("help",
        aliases=[],
        parents=[common_parser],
        formatter_class=Formatter,
        help="help")
    parser_help.set_defaults(function=helper.show_topic)
    parser_help.set_defaults(complete_function=helper.complete_help_topics)

    parser_help.add_argument('topic',
        nargs='?',
        default='general',
        choices=helper.get_topics(),
        help="help topic")

    ### Bash completion 
    def generate_completion(parser, filename, manager):
        if filename == '-':
            filename = None
        from zapper.utils.argparse_completion import complete
        complete(
            parser=top_level_parser,
            filename=filename,
            complete_function_name='complete_function',
            complete_add_arguments_name='complete_add_arguments',
            progname=os.path.basename(sys.argv[0]),
            activate_complete_function="ZAPPER_COMPLETE_FUNCTION=true ",
            skip_keys=['completion'],
            )
            
    if enable_completion_option:
        parser_completion = top_level_subparsers.add_parser(
            "completion",
            parents=[common_parser],
            formatter_class=Formatter,
            help="generate completion for {}".format(manager.translation_name))
        parser_completion.set_defaults(function=generate_completion, parser=top_level_parser, manager=manager)

        parser_completion.add_argument(
            "filename",
            type=str,
            default=os.path.join(manager.USER_RC_DIR, 'completion.{}'.format(manager.translation_name)),
            nargs='?',
            help="output filename")


    ### Package_options
    parser_package_option = {}
    package_option_subparsers = {}
    for option, (parser_name, parser_aliases) in package_options.items():
        parser_package_option[option] =  top_level_subparsers.add_parser(parser_name,
            aliases=parser_aliases,
            parents=[common_parser],
            formatter_class=Formatter,
            help="packages' {0}".format(option))
    
        package_option_subparsers[option] = parser_package_option[option].add_subparsers(
            description="{0} subcommands.".format(option.title()))

    ### Config subparser
    parser_config =  top_level_subparsers.add_parser("config",
        aliases=[],
        parents=[common_parser],
        formatter_class=Formatter,
        help="default values for some command line options")
    #parser_config.set_defaults(default_function=manager.show_current_config, keys=None)

    config_subparsers = parser_config.add_subparsers(
        description="Config subcommand.")

    ### Host subparser
    parser_host = top_level_subparsers.add_parser("host",
        aliases=[],
        parents=[common_parser],
        formatter_class=Formatter,
        help="host configuration; only available for administrators")

    host_subparsers = parser_host.add_subparsers(
        description="Host subcommand.")

    parser_host_package_option = {}
    host_package_option_subparsers = {}
    for option, (parser_name, parser_aliases) in package_options.items():
        parser_host_package_option[option] = host_subparsers.add_parser(parser_name,
            aliases=parser_aliases,
            formatter_class=Formatter,
            help="host default packages' {0}".format(option))

        host_package_option_subparsers[option] = parser_host_package_option[option].add_subparsers(
            description="Host {0} management.".format(option.title()))

    parser_host_config = host_subparsers.add_parser("config",
        aliases=[],
        formatter_class=Formatter,
        help="host default values")
    #parser_host_config.set_defaults(default_function=manager.show_host_config, keys=None)

    host_config_subparsers = parser_host_config.add_subparsers(
        description="Host default values management.")

    ### User subparser
    parser_user = top_level_subparsers.add_parser("user",
        aliases=[],
        parents=[common_parser],
        formatter_class=Formatter,
        help="user configuration")

    user_subparsers = parser_user.add_subparsers(
        description="User subcommand")
    
    parser_user_package_option = {}
    user_package_option_subparsers = {}
    for option, (parser_name, parser_aliases) in package_options.items():
        parser_user_package_option[option] = user_subparsers.add_parser(parser_name,
            aliases=parser_aliases,
            formatter_class=Formatter,
            help="user default packages' {0}".format(option))

        user_package_option_subparsers[option] = parser_user_package_option[option].add_subparsers(
            description="User {0} management.".format(option.title()))

    parser_user_config = user_subparsers.add_parser("config",
        aliases=[],
        formatter_class=Formatter,
        help="user default values")
    #parser_user_config.set_defaults(default_function=manager.show_user_config, keys=None)

    user_config_subparsers = parser_user_config.add_subparsers(
        description="User default values management.")

    ### Session subparser
    parser_session = top_level_subparsers.add_parser("session",
        aliases=[],
        parents=[common_parser],
        formatter_class=Formatter,
        help="session management")

    session_subparsers = parser_session.add_subparsers(
        description="Session subcommand.")

    parser_session_create = session_subparsers.add_parser("create",
        aliases=[],
        parents=[common_parser],
        formatter_class=Formatter,
        help="create a new session")
    parser_session_create.set_defaults(function=manager.create_session)
    
    parser_session_load = session_subparsers.add_parser("load",
        aliases=[],
        parents=[common_parser],
        formatter_class=Formatter,
        help="load an existing session")
    parser_session_load.set_defaults(function=manager.load_session)
    
    parser_session_delete = session_subparsers.add_parser("delete",
        aliases=[],
        parents=[common_parser],
        formatter_class=Formatter,
        help="delete existing sessions")
    parser_session_delete.set_defaults(function=manager.delete_sessions)
    
    parser_session_new = session_subparsers.add_parser("new",
        parents=[common_parser],
        formatter_class=Formatter,
        help="create and load a new session")
    parser_session_new.set_defaults(function=manager.new_session)
    
    parser_session_available = session_subparsers.add_parser("avail",
        aliases=[],
        parents=[common_parser, session_format_parser],
        formatter_class=Formatter,
        help="list all available sessions")
    parser_session_available.add_argument("--no-persistent", "-P",
        dest="persistent",
        action="store_true",
        default=None,
        help="list persistent sessions")
    parser_session_available.add_argument("--no-temporary", "-T",
        dest="temporary",
        action="store_true",
        default=None,
        help="list temporary sessions")
    parser_session_available.set_defaults(function=manager.show_available_sessions)

    parser_session_info = session_subparsers.add_parser("info",
        aliases=[],
        parents=[common_parser],
        formatter_class=Formatter,
        help="show information about the current session")
    parser_session_info.set_defaults(function=manager.session_info)

    parser_session_copy = session_subparsers.add_parser("copy",
        parents=[common_parser],
        formatter_class=Formatter,
        help="copy sessions")
    parser_session_copy.set_defaults(function=manager.copy_sessions)

    for subparser in (parser_session_load, ):
        subparser.add_argument("session_name",
            type=manager.SessionName,
            default=None,
            help="session name")

    for subparser in (parser_session_create, parser_session_new, parser_session_info):
        subparser.add_argument("session_name",
            type=manager.SessionName,
            nargs='?',
            default=None,
            help="session name")

    for subparser in (parser_session_create, parser_session_new):
        subparser.add_argument("--description",
            metavar='D',
            default='',
            help="session description")

    for subparser in (parser_session_copy, ):
        subparser.add_argument("session_name",
            type=manager.SessionName,
            nargs='+',
            default=None,
            help="session names")

    for subparser in (parser_session_delete, ):
        subparser.add_argument("session_name",
            type=manager.SessionName,
            nargs='*',
            default=None,
            help="session names")

    for subparser in (parser_session_info, parser_session_delete, parser_session_load):
        subparser.set_defaults(complete_function=manager.complete_available_sessions)

    for subparser in (parser_session_delete, parser_session_load):
        subparser.set_defaults(complete_add_arguments=['dummy'])

    parser_session_package_option = {}
    session_package_option_subparsers = {}
    for option, (parser_name, parser_aliases) in package_options.items():
        parser_session_package_option[option] = session_subparsers.add_parser(parser_name,
            aliases=parser_aliases,
            formatter_class=Formatter,
            help="session default packages' {0}".format(option))

        session_package_option_subparsers[option] = parser_session_package_option[option].add_subparsers(
            description="Session {0} management.".format(option.title()))

    parser_session_config = session_subparsers.add_parser("config",
        aliases=[],
        formatter_class=Formatter,
        help="session default values")
    #parser_session_config.set_defaults(default_function=manager.show_session_config, keys=None)

    session_config_subparsers = parser_session_config.add_subparsers(
        description="Session default values management.")

    ### Update
    for subparsers in session_subparsers, :
        parser_sync = subparsers.add_parser(
            "sync",
            parents=[common_parser],
            formatter_class=Formatter,
            help="sync current session")
        parser_sync.set_defaults(function=manager.sync_session)

    for option in package_options:
        parser_package_option_show = {}
        for subparsers in package_option_subparsers[option], host_package_option_subparsers[option], user_package_option_subparsers[option], session_package_option_subparsers[option]:
            parser_package_option_show[subparsers] = subparsers.add_parser("show",
                parents=[common_parser],
                formatter_class=Formatter,
                help="show current packages {}".format(option))
            parser_package_option_show[subparsers].add_argument("keys",
                nargs='*',
                help="show keys")
        
        parser_package_option_show[package_option_subparsers[option]].set_defaults(function=manager.show_current_package_option, option=option)
        parser_package_option_show[host_package_option_subparsers[option]].set_defaults(function=manager.show_host_package_option, option=option)
        parser_package_option_show[user_package_option_subparsers[option]].set_defaults(function=manager.show_user_package_option, option=option)
        parser_package_option_show[session_package_option_subparsers[option]].set_defaults(function=manager.show_session_package_option, option=option)


        parser_package_option_set = {}
        parser_package_option_reset = {}
        mutable_package_option_subparsers = []
        if admin_mode:
            mutable_package_option_subparsers.append(host_package_option_subparsers[option])
        mutable_package_option_subparsers.extend((user_package_option_subparsers[option], session_package_option_subparsers[option]))
    
        for subparsers in mutable_package_option_subparsers:
            parser_package_option_set[subparsers] = subparsers.add_parser("set",
                parents=[common_parser],
                formatter_class=Formatter,
                help="set packages' {}".format(option))
            parser_package_option_set[subparsers].add_argument("key_values",
                nargs='*',
                help="set key=value pairs")
            parser_package_option_reset[subparsers] = subparsers.add_parser("reset",
                parents=[common_parser],
                help="reset packages' {}".format(option))
            parser_package_option_reset[subparsers].add_argument("keys",
                nargs='*',
                help="reset keys")
    
        if admin_mode:
            parser_package_option_set[host_package_option_subparsers[option]].set_defaults(function=manager.set_host_package_option, option=option)
            parser_package_option_reset[host_package_option_subparsers[option]].set_defaults(function=manager.reset_host_package_option, option=option)
     
        parser_package_option_set[user_package_option_subparsers[option]].set_defaults(function=manager.set_user_package_option, option=option)
        parser_package_option_reset[user_package_option_subparsers[option]].set_defaults(function=manager.reset_user_package_option, option=option)
    
        parser_package_option_set[session_package_option_subparsers[option]].set_defaults(function=manager.set_session_package_option, option=option)
        parser_package_option_reset[session_package_option_subparsers[option]].set_defaults(function=manager.reset_session_package_option, option=option)
    
    for option in ('version_defaults', ):
        parser_package_option_show[package_option_subparsers[option]].set_defaults(
            complete_function=manager.complete_version_defaults)

        if admin_mode:
            parser_package_option_set[host_package_option_subparsers[option]].set_defaults(
                complete_function=manager.complete_product_names,
                complete_add_arguments=['dummy'])

            parser_package_option_reset[host_package_option_subparsers[option]].set_defaults(
                complete_function=manager.complete_host_version_defaults)

        parser_package_option_set[user_package_option_subparsers[option]].set_defaults(
            complete_function=manager.complete_product_names,
            complete_add_arguments=['dummy'])

        parser_package_option_reset[user_package_option_subparsers[option]].set_defaults(
            complete_function=manager.complete_user_version_defaults)

        parser_package_option_set[session_package_option_subparsers[option]].set_defaults(
            complete_function=manager.complete_product_names,
            complete_add_arguments=['dummy'])

        parser_package_option_reset[session_package_option_subparsers[option]].set_defaults(
            complete_function=manager.complete_session_version_defaults)


    parser_config_show = {}
    parser_config_get = {}
    for subparsers in (config_subparsers, host_config_subparsers, user_config_subparsers, session_config_subparsers):
        parser_config_show[subparsers] = subparsers.add_parser("show",
            parents=[common_parser],
            formatter_class=Formatter,
            help="show current value")
        parser_config_show[subparsers].add_argument("keys",
            nargs='*',
            help="show keys")
        parser_config_get[subparsers] = subparsers.add_parser("get",
            parents=[common_parser],
            formatter_class=Formatter,
            help="get current value")
        parser_config_get[subparsers].add_argument("key",
            help="get key")
    
    parser_config_show[config_subparsers].set_defaults(
        function=manager.show_current_config,
        complete_function=manager.complete_config_keys)
    parser_config_show[host_config_subparsers].set_defaults(
        function=manager.show_host_config,
        complete_function=manager.complete_host_config_keys)
    parser_config_show[user_config_subparsers].set_defaults(
        function=manager.show_user_config,
        complete_function=manager.complete_user_config_keys)
    parser_config_show[session_config_subparsers].set_defaults(
        function=manager.show_session_config,
        complete_function=manager.complete_session_config_keys)

    parser_config_get[config_subparsers].set_defaults(
        function=manager.get_current_config,
        complete_function=manager.complete_config_keys,
        complete_add_arguments=['dummy'])
    parser_config_get[host_config_subparsers].set_defaults(
        function=manager.get_host_config,
        complete_function=manager.complete_host_config_keys,
        complete_add_arguments=['dummy'])
    parser_config_get[user_config_subparsers].set_defaults(
        function=manager.get_user_config,
        complete_function=manager.complete_user_config_keys,
        complete_add_arguments=['dummy'])
    parser_config_get[session_config_subparsers].set_defaults(
        function=manager.get_session_config,
        complete_function=manager.complete_session_config_keys,
        complete_add_arguments=['dummy'])

    parser_config_set = {}
    parser_config_reset = {}
    mutable_config_subparsers = []
    if admin_mode:
        mutable_config_subparsers.append(host_config_subparsers)
    mutable_config_subparsers.extend((user_config_subparsers, session_config_subparsers))

    for subparsers in mutable_config_subparsers:
        parser_config_set[subparsers] = subparsers.add_parser("set",
            parents=[common_parser],
            formatter_class=Formatter,
            help="set default values")
        parser_config_set[subparsers].add_argument("key_values",
            nargs='*',
            help="set key=value pairs")
        parser_config_reset[subparsers] = subparsers.add_parser("reset",
            parents=[common_parser],
            formatter_class=Formatter,
            help="reset default values")
        parser_config_reset[subparsers].add_argument("keys",
            nargs='*',
            help="reset keys")

    if admin_mode:
        parser_config_set[host_config_subparsers].set_defaults(
            function=manager.set_host_config,
            complete_function=manager.complete_host_config_keys,
            complete_add_arguments=['dummy'])
        parser_config_reset[host_config_subparsers].set_defaults(
            function=manager.reset_host_config,
            complete_function=manager.complete_host_config_keys)
 
    parser_config_set[user_config_subparsers].set_defaults(
            function=manager.set_user_config,
            complete_function=manager.complete_user_config_keys,
            complete_add_arguments=['dummy'])
    parser_config_reset[user_config_subparsers].set_defaults(
            function=manager.reset_user_config,
            complete_function=manager.complete_user_config_keys)

    parser_config_set[session_config_subparsers].set_defaults(
            function=manager.set_session_config,
            complete_function=manager.complete_session_config_keys,
            complete_add_arguments=['dummy'])
    parser_config_reset[session_config_subparsers].set_defaults(
            function=manager.reset_session_config,
            complete_function=manager.complete_session_config_keys)

    ### Package subparser
    parser_package_show_available_packages = top_level_subparsers.add_parser("avail",
        aliases=[],
        parents=[common_parser, package_format_parser],
        formatter_class=Formatter,
        help="list available packages")

    parser_package_show_available_packages.add_argument("package_labels",
        default=[],
        nargs='*',
        help='package labels')
    parser_package_show_available_packages.set_defaults(function=manager.show_available_packages)

    parser_package_show_loaded_packages = top_level_subparsers.add_parser("list",
        aliases=[],
        parents=[common_parser, package_format_parser],
        formatter_class=Formatter,
        help="list loaded packages")
    parser_package_show_loaded_packages.set_defaults(function=manager.show_loaded_packages)

    parser_package_show_package = top_level_subparsers.add_parser("show",
        aliases=[],
        parents=[common_parser],
        formatter_class=Formatter,
        help="show package content")
    parser_package_show_package.add_argument("package_label",
        help="package label")
    parser_package_show_package.set_defaults(function=manager.show_package)

    parser_package_load = top_level_subparsers.add_parser("load",
        parents=[common_parser],
        formatter_class=Formatter,
        help="add packages to current session",
        epilog="""\
[Resolution aggressivity level]:
  > 0: missing requirements are searched in available packages
  > 1: missing requirements are searched in defined packages
""")
    parser_package_load.set_defaults(function=manager.load_package_labels)

    parser_package_unload = top_level_subparsers.add_parser("unload",
        aliases=[],
        parents=[common_parser],
        formatter_class=Formatter,
        help="remove packages from current session",
        epilog="""\
[Resolution aggressivity level]:
  > 0: packages with unsatisfied requirements after removal will be
       automatically removed
""")
    parser_package_unload.set_defaults(function=manager.unload_package_labels)

    parser_package_clear = top_level_subparsers.add_parser("clear",
        parents=[common_parser],
        formatter_class=Formatter,
        help="unload all loaded packages from current session")
    parser_package_clear.set_defaults(function=manager.clear_packages)

    for key, subparser in ('load', parser_package_load), ('unload', parser_package_unload):
        subparser.add_argument("package_labels",
            type=str,
            nargs='+',
            default=None,
            help="package name")
        subparser.add_argument("--resolve", "-r",
            dest="resolution_level",
            action="count",
            default=manager.get_config_key('resolution_level'),
            help="automatically resolve missing requirements (repeat to increase aggressivity level)")
        subparser.add_argument("--subpackages", "-s",
            dest="subpackages",
            action="store_true",
            default=manager.get_config_key('subpackages'),
            help="automatically {0} all suite's packages".format(key))
     
    for subparser_name, subparser in ('load', parser_package_load), ('unload', parser_package_unload), ('clear', parser_package_clear):
        subparser.add_argument("--simulate",
            dest="simulate",
            action="store_true",
            default=False,
            help="show only changes")

        subparser.add_argument("--sticky", "-S",
            dest="sticky",
            action="store_true",
            default=False,
            help="{0} sticky packages".format(subparser_name))

    for parser in (parser_package_load, parser_package_show_package, parser_package_show_available_packages):
        parser.set_defaults(complete_function=manager.complete_available_packages, complete_add_arguments=['dummy'])

    for parser in (parser_package_unload, ):
        parser.set_defaults(complete_function=manager.complete_loaded_packages, complete_add_arguments=['dummy'])

### No more parsers!
    return top_level_parser

def zapper_main():
    manager = create_manager()
    top_level_parser = create_top_level_parser(manager)
    try:
        autocomplete_monkey_patch(top_level_parser)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print(exc_value)
        # ignoring these exceptions, since this is not mandatory
        pass

    args = top_level_parser.parse_args()

    _set_global_flags(
        _ZAPPER_COMPLETE_FUNCTION,
        quiet=args.quiet,
        verbose=args.verbose,
        debug=args.debug,
        trace=args.trace,
    )
    manager.set_dry_run(args.dry_run)
    manager.set_force(args.force)
    manager.set_show_header(args.show_header, args.show_header_if_empty)
    manager.set_show_translation(args.show_translation)
    manager.set_package_format(args.package_format)
    manager.set_package_dir_format(args.package_dir_format)
    manager.set_session_format(args.session_format)
    manager.set_package_sort_keys(args.package_sort_keys)
    manager.set_package_dir_sort_keys(args.package_dir_sort_keys)
    manager.set_session_sort_keys(args.session_sort_keys)

    if 'persistent' in args and 'temporary' in args:
        if args.persistent is None:
            if args.temporary is None:
                args.persistent = True
                args.temporary = True
            else:
                args.persistent = False
        if args.temporary is None:
            args.temporary = False
    p_args = args._get_args()
    n_args = dict(args._get_kwargs())
    for key in {'function', 'quiet', 'verbose', 'debug', 'trace', 'full_label',
                'dry_run', 'force', 'show_header', 'show_header_if_empty', 'show_translation',
                'package_format', 'session_format', 'package_dir_format',
                'package_sort_keys', 'package_dir_sort_keys', 'session_sort_keys',
                'complete_function', 'complete_add_arguments'}:
        if key in n_args:
            del n_args[key]

    manager.initialize()

    complete_function = getattr(args, 'complete_function', None)
    if complete_function and os.environ.get("ZAPPER_COMPLETE_FUNCTION", ""):
        try:
            args.complete_function(*p_args, **n_args)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            trace()
            LOGGER.critical("{0}: {1}".format(exc_type.__name__, exc_value))
    else:
        function = getattr(args, 'function', None)
        if function is None:
            LOGGER.critical("invalid command line (this is probably due to a bug in argparse)")
            sys.exit(1)
        try:
            function(*p_args, **n_args)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            trace()
            #sys.stderr.write("ERR: {}: {}\n".format(exc_type.__name__, exc_value))
            LOGGER.critical("{0}: {1}".format(exc_type.__name__, exc_value))
            sys.exit(1)
        else:
            manager.finalize()

if __name__ == "__main__":
    zapper_main()
