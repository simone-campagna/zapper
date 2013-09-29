from zapper.package_file import *


ylib = Product('ylib', 'library')
zlib = Product('zlib', 'library')
ymodel = Product('ymodel', 'application')

for version in '11.0', '12.1':
    intel = Suite('intel', version)
    intel.add_conflicting_tag('compiler-suite')

    ylib_1_0 = Package(ylib, '1.0', suite=intel)
    ylib_1_0.var_set("YLIB_HOME", "/opt/intel-{}/ylib-1.0".format(version))

    ylib_1_1_beta = Package(ylib, '1.1-beta', suite=intel)
    ylib_1_1_beta.var_set("YLIB_HOME", "/opt/intel-{}/ylib-1.1-beta".format(version))

    zlib_2_1 = Package(zlib, '2.1', suite=intel)
    zlib_2_1.var_set("ZLIB_HOME", "/opt/intel-{}/zlib-2.1".format(version))
    zlib_2_1.requires('ylib', VERSION <= '1.0')

    zlib_2_3 = Package(zlib, '2.3', suite=intel)
    zlib_2_3.var_set("ZLIB_HOME", "/opt/intel-{}/zlib-2.3".format(version))
    zlib_2_3.requires('ylib', VERSION >= '1.1')

    ymodel_8_1_0 = Package(ymodel, '8.1.0', suite=intel)
    ymodel_8_1_0.var_set("YMODEL_HOME", "/opt/gnu-{}/ymodel-8.1.0".format(version))
    ymodel_8_1_0.requires('zlib', VERSION >= '2.3')

