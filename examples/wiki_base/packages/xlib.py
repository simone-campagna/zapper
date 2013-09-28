from zapper.package_file import *
import os

xlib = Product('xlib', 'application')

xlib_2_4 = Package(xlib, '2.4')
xlib_2_4.var_set("XLIB_HOME", os.path.expandvars("/opt/install/xlib-2.4"))
xlib_2_4.path_prepend("LD_LIBRARY_PATH", os.path.expandvars("/opt/install/xlib-2.4/lib"))
xlib_2_4.var_set("XLIB_INCLUDE", os.path.expandvars("/opt/install/xlib-2.4/include"))

xlib_2_5 = Package(xlib, '2.5')
xlib_2_5.var_set("XLIB_HOME", os.path.expandvars("/opt/install/xlib-2.5"))
xlib_2_5.path_prepend("LD_LIBRARY_PATH", os.path.expandvars("/opt/install/xlib-2.5/lib"))
xlib_2_5.var_set("XLIB_INCLUDE", os.path.expandvars("/opt/install/xlib-2.5/include"))

xlib_2_6 = Package(xlib, '2.6')
xlib_2_6.var_set("XLIB_HOME", os.path.expandvars("/opt/install/xlib-2.6"))
xlib_2_6.path_prepend("LD_LIBRARY_PATH", os.path.expandvars("/opt/install/xlib-2.6/lib"))
xlib_2_6.var_set("XLIB_INCLUDE", os.path.expandvars("/opt/install/xlib-2.6/include"))
