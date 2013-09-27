from zapper.package_file import *

intel = Suite('intel', NULL_VERSION)
intel.add_conflicting_tag('compiler-suite')

ylib = Product('ylib', 'library')
zlib = Product('zlib', 'library')
zmodel = Product('zmodel', 'application')

for version in '11.0', '12.1':
    version_name = version.replace('.', '_')
    intel_version = Suite(version_name, NULL_VERSION, suite=intel)
    intel_version.add_conflicting_tag('intel-suite')

    ylib_1_0 = Package(ylib, '1.0', suite=intel_version)
    ylib_1_0.var_set("YLIB_HOME", "/opt/intel-{}/ylib-1.0".format(version))

    ylib_1_1_beta = Package(ylib, '1.1-beta', suite=intel_version)
    ylib_1_1_beta.var_set("YLIB_HOME", "/opt/intel-{}/ylib-1.1-beta".format(version))

    zlib_2_1 = Package(zlib, '2.1', suite=intel_version)
    zlib_2_1.var_set("ZLIB_HOME", "/opt/intel-{}/zlib-2.1".format(version))
    zlib_2_1.requires('ylib', VERSION <= '1.0')

    zlib_2_3 = Package(zlib, '2.3', suite=intel_version)
    zlib_2_3.var_set("ZLIB_HOME", "/opt/intel-{}/zlib-2.3".format(version))
    zlib_2_3.requires('ylib', VERSION >= '1.1')

    zmodel_10_1 = Package(zmodel, '10.1', suite=intel_version)
    zmodel_10_1.var_set("ZMODEL_HOME", "/opt/intel-{}/zmodel-10.1".format(version))
    zmodel_10_1.requires('zlib', VERSION >= '2.0')