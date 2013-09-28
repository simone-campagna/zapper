from zapper.package_file import *

pkg2 = Product('pkg2', 'application')

pkg2_5_4_3 = Package(pkg2, '5.4.3')
pkg2_5_4_3.var_set("PKG2_HOME", "/opt/install/pkg2-5.4.3")
