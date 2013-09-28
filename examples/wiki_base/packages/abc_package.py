from zapper.package_file import *
import os

abc = Product('abc', 'application')

abc_1_0_4 = Package(abc, '1.0.4')
abc_1_0_4.var_set("ABC_HOME", os.path.expandvars("/opt/install/abc-1.0"))
abc_1_0_4.path_prepend("PATH", os.path.expandvars("/opt/install/abc-1.0/bin"))
abc_1_0_4.path_prepend("LD_LIBRARY_PATH", os.path.expandvars("/opt/install/abc-1.0/lib"))
abc_1_0_4.requires((NAME == 'xlib') & (VERSION >= '2.5'))
