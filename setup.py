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
import glob
import shutil
import difflib
import filecmp
import getpass
import tempfile
import collections

ZAPPER_VERSION = "0.1"

dirname = os.path.dirname(os.path.abspath(sys.argv[0]))
py_dirname = os.path.join(dirname, "lib", "python")
sys.path.insert(0, py_dirname)

from zapper.manager import Manager
from zapper.utils.argparse_completion import COMPLETION_VERSION

from distutils.core import setup
from distutils import log
from distutils.command.install_data import install_data
from distutils.command.install_scripts import install_scripts
from distutils.cmd import Command

FILES_TO_BACKUP = set()
def add_file_to_backup(filename, dirname):
    global FILES_TO_BACKUP
    FILES_TO_BACKUP.add(os.path.relpath(os.path.normpath(os.path.abspath(filename)), dirname))

shell_setup_files = []
shell_setup_subdir = 'etc/profile.d'
for shell_setup_file in glob.glob(os.path.join(dirname, shell_setup_subdir, 'zapper.*')):
    shell_setup_files.append(shell_setup_file)
    add_file_to_backup(shell_setup_file, dirname)

host_config_file = os.path.join(dirname, 'etc', 'zapper', 'host.config')
add_file_to_backup(host_config_file, dirname)

class pre_command(object):
    def run(self):
        install_cmd = self.get_finalized_command('install')
        self.install_base = os.path.normpath(os.path.abspath(getattr(install_cmd, 'install_base')))
        self.admin_user = getpass.getuser()
        return super().run()

class subst_command(Command):
    def _init(self):
        if not hasattr(self, 'r_list'):
            v_dict = {
                'ZAPPER_VERSION':             ZAPPER_VERSION,
                'ZAPPER_HOME_DIR':            self.install_base,
                'ZAPPER_RC_DIR_NAME':         Manager.RC_DIR_NAME,
                'ZAPPER_ADMIN_USER':          self.admin_user,
                'PYTHON_EXECUTABLE':          sys.executable,
                'ZAPPER_COMPLETION_VERSION':  COMPLETION_VERSION,
            }
            self.r_list = []
            for key, val in v_dict.items():
                self.r_list.append((re.compile(r"@{0}@".format(key)), str(val)))

    def transform_file(self, infile, outfile):
        self._init()
        log.info("substituting {0} -> {1}...".format(infile, outfile))
        with open(outfile, "w") as f_out, open(infile, "r") as f_in:
            source = f_in.read()
            for regular_expression, substitution in self.r_list:
                source = regular_expression.sub(substitution, source)
                #print("___>", substitution)
            f_out.write(source)

    def _backup_file(self, infile, outfile):
        if os.path.exists(outfile):
            if os.path.isdir(outfile):
                outfile = os.path.join(outfile, os.path.basename(infile))
        if os.path.exists(outfile):
            outfile = os.path.normpath(os.path.abspath(outfile))
            outfile_relpath = os.path.relpath(outfile, self.install_dir)
            #print("--- {} in {}: {}".format(outfile, FILES_TO_BACKUP, outfile in FILES_TO_BACKUP))
            if outfile_relpath in FILES_TO_BACKUP:
                #print("BACKUP: {}".format(outfile))
                if not filecmp.cmp(infile, outfile):
                    overwrite = False
                    while True:
                        answer = input("=" * 70  + "\nOverwrite existing file {}? [yes/no/diff] ".format(outfile))
                        if answer == 'yes': 
                            overwrite = True
                            break
                        elif answer == 'no': 
                            overwrite = False
                            break
                        elif answer == 'diff': 
                            with open(infile, 'r') as fa, open(outfile, 'r') as fb:
                                sys.stdout.writelines(difflib.context_diff(fa.readlines(), fb.readlines(), fromfile=infile, tofile=outfile))
                            continue
                        else:
                            sys.stderr.write("please, answer 'yes', 'no' or 'diff'\n")
                    if overwrite:
                        shutil.copy(outfile, outfile + '.bck')
                        return True
                    else:
                        return False
        return True
                     
                        
                    
        
    def copy_file(self, infile, outfile, preserve_mode=1, preserve_times=1, link=None, level=1):
        with tempfile.TemporaryDirectory(prefix=os.path.basename(infile)) as tmpdir:
            tmpfile = os.path.join(tmpdir, os.path.basename(infile))
            self.transform_file(infile, tmpfile)
            copy = self._backup_file(tmpfile, outfile)
            if copy:
                result = super().copy_file(tmpfile, outfile, preserve_mode=preserve_mode, preserve_times=preserve_times, link=link, level=level)
            else:
                result = (outfile, False)
        return result

    def copy_tree(self, infile, outfile, preserve_mode=1, preserve_times=1,
                  preserve_symlinks=0, level=1):
        with tempfile.TemporaryDirectory(prefix=os.path.basename(infile)) as tmpdir:
            for dirpath, dirnames, filenames in os.walk(infile):
                rdir = os.path.relpath(dirpath, infile)
                tmpd = os.path.join(tmpdir, rdir)
                if not os.path.isdir(tmpd):
                    os.makedirs(tmpd)
                for filename in filenames:
                    in_filename = os.path.join(dirpath, filename)
                    out_filename = os.path.join(tmpd, filename)
                    self.transform_file(in_filename, out_filename)
            result = super().copy_tree(tmpdir, outfile, preserve_mode=preserve_mode, preserve_times=preserve_times, preserve_symlinks=preserve_symlinks, level=level)
        return result

class subst_install_data(pre_command, install_data, subst_command):
    pass

class subst_install_scripts(pre_command, install_scripts, subst_command):
    pass

setup(
    name = "zapper",
    version = ZAPPER_VERSION,
    requires = [],
    description = "Tool to manage unix environment",
    author = "Simone Campagna",
    author_email = "simone.campagna@tiscali.it",
    url="https://github.com/simone-campagna/unix-sessions",
    packages = ["zapper", "zapper.translators", "zapper.utils", "zapper.application"],
    package_dir = {"zapper": "lib/python/zapper"},
    scripts = [
	'bin/zapper',
    ],
    data_files = [
        ('etc/zapper', glob.glob('etc/zapper/*.config')),
        (shell_setup_subdir, shell_setup_files),
        ('etc/zapper/packages', []),
        ('shared/zapper/examples/wiki_example/packages', glob.glob('examples/wiki_example/packages/*.py')),
        ('shared/zapper/examples/wiki_base/packages', glob.glob('examples/wiki_base/packages/*.py')),
        ('shared/zapper/examples/wiki_simple_suite/packages', glob.glob('examples/wiki_simple_suite/packages/*.py')),
        ('shared/zapper/examples/wiki_suites/packages', glob.glob('examples/wiki_suites/packages/*.py')),
        ('shared/zapper/examples/wiki_subsuites/packages', glob.glob('examples/wiki_subsuites/packages/*.py')),
    ],
    cmdclass = {
        'install_data': subst_install_data,
        'install_scripts': subst_install_scripts,
    },
)

