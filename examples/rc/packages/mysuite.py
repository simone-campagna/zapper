from unix_sessions.package import Package
from unix_sessions.suite import Suite
from unix_sessions.transition import *

print("# MySuite...")

libalfa = Package('alfa', '0.3', 'lib')
libalfa.var_set('ALFA', 10)
libalfa.path_append('LD_LIBRARY_PATH', '/usr/lib/alfa-0.3')

libbeta = Package('beta', '0.2', 'lib')
libbeta.path_append('LD_LIBRARY_PATH', '/usr/lib/beta-0.2')

xyz = Package('xyz', '1.3.2-rc1', 'application')
xyz.path_append('PATH', '/usr/lib/xyz-1.3.2')
xyz.path_remove('PATH', '/usr/xyz-old')

xyz.requires('alfa', lambda package: package.version >= '0.2')
xyz.prefers('beta', lambda package: package.version >= '0.2')
xyz.conflicts('xyz')

abc = Package('abc', '0.0.1', 'tool')
abc.path_append('PATH', '/usr/lib/abc-0.0.1')
abc.var_set('ABC_HOME', '/home/simone/abc-0.0.1')
abc.var_unset('DEF')

mysuite = Suite('mysuite', '0.1', 'tool')
mysuite.add_package(abc)
mysuite.add_package(xyz)

