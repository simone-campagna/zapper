from zapper.package_file import *
import os

pkg0 = Product('pkg0', 'application')

pkg0_3_2_1 = Package(pkg0, '3.2.1')
pkg0_3_2_1.var_set("PKG0_HOME", os.path.expandvars("/opt/install/pkg0-3.2.1"))
pkg0_3_2_1.requires((NAME == 'pkg1') & (VERSION >= '4.3'))
