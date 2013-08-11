from unix_sessions.package import Package
from unix_sessions.suite import Suite
from unix_sessions.transition import *

print("HERE")

libalfa = Package('alfa', '0.3', 'lib')
libalfa.setenv('ALFA', 10)
libalfa.append_path('LD_LIBRARY_PATH', '/usr/lib/alfa-0.3')

libbeta = Package('beta', '0.2', 'lib')
libbeta.append_path('LD_LIBRARY_PATH', '/usr/lib/beta-0.2')

xyz = Package('xyz', '1.3.2-rc1', 'application')
xyz.append_path('PATH', '/usr/lib/xyz-1.3.2')

xyz.requires('alfa', lambda package: package.version >= '0.2')
xyz.prefers('beta', lambda package: package.version >= '0.2')
xyz.conflicts('xyz')

abc = Package('abc', '0.0.1', 'tool')
abc.append_path('PATH', '/usr/lib/abc-0.0.1')

mysuite = Suite('mysuite', '0.1', 'tool')
mysuite.add_component(abc)
mysuite.add_component(xyz)

#from unix_sessions.component import Component
#print(Component.REGISTRY._reg)
