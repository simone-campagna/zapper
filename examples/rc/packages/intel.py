from unix_sessions.package_file import *

intel = Suite('intel', NULL_VERSION)
intel.add_conflicting_tag('compiler-suite')

for version in '11.0', '12.1':
    version_name = version.replace('.', '_')
    intel_version = Suite(version_name, NULL_VERSION, suite=intel)
    intel.add_conflicting_tag('intel-suite')
    #intel.conflicts(HAS_TAG('compiler'))
    
    libfoo = PackageFamily('libfoo', 'library')

    libfoo_0_5 = Package(libfoo, '0.5', suite=intel_version)
    libfoo_0_5.var_set("FOO_HOME", "/intel-{0}/foo-0.5".format(version))

    libfoo_0_5_3 = Package(libfoo, '0.5.3', suite=intel_version)
    libfoo_0_5_3.var_set("FOO_HOME", "/intel-{0}/foo-0.5.3".format(version))

    libbar = PackageFamily('libbar', 'library')

    libbar_1_0_2 = Package(libbar, '1.0.2', suite=intel_version)
    libbar_1_0_2.var_set("BAR_HOME", "/intel-{0}/bar-1.0.2".format(version))

    baz = PackageFamily('baz', 'tool')

    baz_1_1 = Package(baz, '1.1', suite=intel_version)
    baz_1_1.var_set("BAZ_HOME", "/intel-{0}/baz-1.1".format(version))
    baz_1_1.requires('libfoo', VERSION > '0.5')
    baz_1_1.requires(libbar_1_0_2)

    hello_world = PackageFamily("hello_world", 'application')

    hello_world_0_0_1_beta = Package(hello_world, '0.0.1-beta', suite=intel_version)
    hello_world_0_0_1_beta.var_set("HELLO_WORLD_HOME", "/intel-{0}/hello_world-0.0.1-beta".format(version))

