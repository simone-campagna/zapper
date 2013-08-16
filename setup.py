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

import os
import re
import sys
import glob
import tempfile

from distutils.core import setup
from distutils import log
from distutils.command.install_data import install_data

class subst_install_data(install_data):
    def run(self):
        install_cmd = self.get_finalized_command('install')
        self.install_base = os.path.normpath(os.path.abspath(getattr(install_cmd, 'install_base')))
        return super().run()

    def copy_file(self, infile, outfile, preserve_mode=1, preserve_times=1, link=None, level=1):
        v_dict = {
            'UXS_HOME_DIR':             self.install_base,
            'PYTHON_EXECUTABLE':        sys.executable,
        }
        r_list = []
        for key, val in v_dict.items():
            r_list.append((re.compile(r"@{0}@".format(key)), val))
        with tempfile.TemporaryDirectory(prefix=os.path.basename(infile)) as tmpdir:
            tmpfile = os.path.join(tmpdir, os.path.basename(infile))
            log.info("substituting {0} -> {1}...".format(infile, tmpfile))
            with open(tmpfile, "w") as f_out, open(infile, "r") as f_in:
                source = f_in.read()
                for regular_expression, substitution in r_list:
                    source = regular_expression.sub(substitution, source)
                f_out.write(source)
                f_out.flush()
            result = super().copy_file(f_out.name, outfile, preserve_mode=preserve_mode, preserve_times=preserve_times, link=link, level=level)
        return result

setup(
    name = "unix-sessions",
    version = "0.1",
    requires = [],
    description = "Tool to manage unix environment",
    author = "Simone Campagna",
    author_email = "simone.campagna@tiscali.it",
    url="https://github.com/simone-campagna/unix-sessions",
    packages = ["unix_sessions", "unix_sessions.serializers", "unix_sessions.utils"],
    package_dir = {"unix_sessions": "lib/python/unix_sessions"},
    scripts = [
	'bin/session',
    ],
    data_files = [
        ('etc/unix-sessions.d', glob.glob('etc/unix-sessions.d/*.rc')),
    ],
    cmdclass = {'install_data': subst_install_data},
)

