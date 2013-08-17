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
import time
import errno
import fcntl
import contextlib

@contextlib.contextmanager
def Lock(filename, mode="r", blocking=True, timeout=10):
    # enter
    lock_op = fcntl.LOCK_EX
    if not blocking:
        lock_op += fcntl.LOCK_NB
    count = 0
    interval = 0.1
    if timeout is not None:
      count = int(round(timeout/interval, 0))
    if count <= 0:
      count = 1
    with open(filename, mode) as f:
        for i in range(count):
            try:
                #fcntl.fcntl(self.fileno(), lock_op, os.O_NDELAY)
                fcntl.lockf(f.fileno(), lock_op)
            except IOError as e:
                if e.errno in (errno.EACCES, errno.EAGAIN):
                    if timeout:
                        time.sleep(interval)
                    continue
            except:
                import traceback
                traceback.print_exc()
                time.sleep(interval)
        yield f
    #exit
        fcntl.lockf(f.fileno(), fcntl.LOCK_UN)

if __name__ == "__main__":
    import sys
    with Lock('a.lock', 'a') as f_out:
        for arg in sys.argv:
            f_out.write(arg + '\n')
        f_out.flush()
        print("sleeping...")
        time.sleep(10)
        print("done.")
        f_out.write("finito!\n")

    
    
