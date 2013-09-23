from zapper.package_file import *
import os

pkg1 = Product('pkg1', 'application')

pkg1_4_2 = Package(pkg1, '4.2')
pkg1_4_2.var_set("PKG1_HOME", os.path.expandvars("/opt/install/pkg1-4.2"))
pkg1_4_2.conflicts(NAME == 'pkg2')

pkg1_4_3_0 = Package(pkg1, '4.3.0')
pkg1_4_3_0.var_set("PKG1_HOME", os.path.expandvars("/opt/install/pkg1-4.3.0"))
pkg1_4_3_0.conflicts(NAME == 'pkg2')

pkg1_4_3_2 = Package(pkg1, '4.3.2')
pkg1_4_3_2.var_set("PKG1_HOME", os.path.expandvars("/opt/install/pkg1-4.3.2"))
pkg1_4_3_2.conflicts(NAME == 'pkg2')

