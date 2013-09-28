from zapper.package_file import *


ylib = Product('ylib', 'library')
zlib = Product('zlib', 'library')

for version in '4.1.2', '4.5.2', '4.7.0':
    gnu = Suite('gnu', version)
    gnu.add_conflicting_tag('compiler-suite')

    ylib_1_0 = Package(ylib, '1.0', suite=gnu)
    ylib_1_0.var_set("YLIB_HOME", "/opt/gnu-{}/ylib-1.0".format(version))

    ylib_1_1_beta = Package(ylib, '1.1-beta', suite=gnu)
    ylib_1_1_beta.var_set("YLIB_HOME", "/opt/gnu-{}/ylib-1.1-beta".format(version))

    zlib_2_1 = Package(zlib, '2.1', suite=gnu)
    zlib_2_1.var_set("ZLIB_HOME", "/opt/gnu-{}/zlib-2.1".format(version))
    zlib_2_1.requires('ylib', VERSION <= '1.0')

    zlib_2_3 = Package(zlib, '2.3', suite=gnu)
    zlib_2_3.var_set("ZLIB_HOME", "/opt/gnu-{}/zlib-2.3".format(version))
    zlib_2_3.requires('ylib', VERSION >= '1.1')

