from zapper.package_file import *

pkg1 = Product('pkg1', 'application')
pkg1.set_short_description("pkg1 is an example")
pkg1.set_long_description("""\
This is an example of a long description for the pkg1 package. The description text will be inherited by all the packages.
A package can override it.""")

pkg1_4_2 = Package(pkg1, '4.2')
pkg1_4_2.var_set("PKG1_HOME", "/opt/install/pkg1-4.2")
pkg1_4_2.conflicts(NAME == 'pkg2')

pkg1_4_3_0 = Package(pkg1, '4.3.0')
pkg1_4_3_0.var_set("PKG1_HOME", "/opt/install/pkg1-4.3.0")
pkg1_4_3_0.conflicts(NAME == 'pkg2')

pkg1_4_3_2 = Package(pkg1, '4.3.2')
pkg1_4_3_2.var_set("PKG1_HOME", "/opt/install/pkg1-4.3.2")
pkg1_4_3_2.conflicts(NAME == 'pkg2')

