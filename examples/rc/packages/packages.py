from zapper.package_file import *

#print("# MySuite...")

libalfa = PackageFamily('alfa', 'xlibrary')
libalfa.set_short_description("This is the alfa package")
libalfa.set_long_description("""Alfa is a dummy package. This is its long description.
The main goal of this package is to show how the long description text is rendered, using the text module.
If it's correctly working, this should be the second paragraph; the first one is just above. The third paragraph is below:

That's all, folks!
""")

libalfa_0_3 = Package(libalfa, '0.3')
libalfa_0_3.var_set('ALFA_HOME', "/home/alfa-0.3")
libalfa_0_3.var_set('ALFA_VERSION', 0.3)
libalfa_0_3.path_append('LD_LIBRARY_PATH', '/usr/lib/alfa-0.3')

libalfa_0_4 = Package(libalfa, '0.4')
libalfa_0_4.var_set('ALFA_HOME', "/home/alfa-0.4")
libalfa_0_4.var_set('ALFA_VERSION', 0.4)
libalfa_0_4.path_append('LD_LIBRARY_PATH', '/usr/lib/alfa-0.4')
libalfa_0_4.long_description = libalfa.long_description + """
This new version 0.4 has many useful new features."""
libalfa_0_4.conflicts(libalfa_0_3)
libalfa_0_4.add_tag('experimental')


libbeta = PackageFamily('beta', 'library')

libbeta_0_2 = Package(libbeta, '0.2')
libbeta_0_2.var_set('BETA_HOME', "/home/beta-0.2")
libbeta_0_2.path_append('LD_LIBRARY_PATH', '/usr/lib/beta-0.2')
libbeta_0_2.requires('alfa', VERSION == '0.3')

libbeta_1_0 = Package(libbeta, '1.0')
libbeta_1_0.var_set('BETA_HOME', "/home/beta-1.0")
libbeta_1_0.path_append('LD_LIBRARY_PATH', '/usr/lib/beta-1.0')
libbeta_1_0.requires('alfa', VERSION >= '0.4')

xyz = PackageFamily('xyz', 'application')

xyz_1_3_2_rc1 = Package(xyz, '1.3.2-rc1')
xyz_1_3_2_rc1.var_set('XYZ_HOME', "/home/xyz-1.3.2")
xyz_1_3_2_rc1.path_append('PATH', '/usr/lib/xyz-1.3.2')
xyz_1_3_2_rc1.path_append('PATH', '/usr/local/sbin')
xyz_1_3_2_rc1.var_set('XYZ_HOME', '/here/is/xyz')

xyz_1_3_2_rc1.requires('beta', VERSION >= '0.2')
xyz_1_3_2_rc1.prefers('alfa', VERSION > '0.2')
xyz_1_3_2_rc1.conflicts('xyz')

abc = PackageFamily('abc0', 'tool')
abc_0_0_1 = Package(abc, '0.0.1')
abc_0_0_1.path_append('PATH', '/usr/lib/abc-0.0.1')
abc_0_0_1.var_set('ABC_HOME', '/home/simone/abc-0.0.1')
abc_0_0_1.var_unset('DEF')
abc_0_0_1.var_unset('LANG')

www = Suite('www', NULL_VERSION)

libalfa_0_2 = Package(libalfa, '0.2', suite=www)
libalfa_0_2.var_set('ALFA_HOME', "/home/www/alfa-0.2")
libalfa_0_2.var_set('ALFA_VERSION', 0.2)
libalfa_0_2.path_append('LD_LIBRARY_PATH', '/usr/lib/www/alfa-0.2')

libalfa_0_3 = Package(libalfa, '0.3', suite=www)
libalfa_0_3.var_set('ALFA_HOME', "/home/www/alfa-0.3")
libalfa_0_3.var_set('ALFA_VERSION', 0.3)
libalfa_0_3.path_append('LD_LIBRARY_PATH', '/usr/lib/www/alfa-0.3')

libalfa_0_7 = Package(libalfa, '0.7', suite=www)
libalfa_0_7.var_set('ALFA_HOME', "/home/www/alfa-0.7")
libalfa_0_7.var_set('ALFA_VERSION', 0.7)
libalfa_0_7.path_append('LD_LIBRARY_PATH', '/usr/lib/www/alfa-0.7')

