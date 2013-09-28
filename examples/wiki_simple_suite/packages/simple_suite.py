from zapper.package_file import *

simple_suite = Suite('simple_suite', NULL_VERSION)
simple_suite.var_set('SIMPLE_SUITE_HOME', '/opt/simple_suite')

foo = Product('foo', 'application')

foo_0_1 = Package('foo', '0.1', suite=simple_suite)
foo_0_1.var_set('FOO_HOME', "/opt/simple_suite/foo-0.1")

pkg0 = Product('pkg0', 'application')

pkg0_0_1 = Package('pkg0', '0.1', suite=simple_suite)
pkg0_0_1.var_set('PKG0_HOME', "/opt/simple_suite/pkg0-0.1")

