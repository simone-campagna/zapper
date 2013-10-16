from zapper.package_file import *
import os

test_var_set = Product('test_var_set', '')
test_var_set_1 = Package(test_var_set, '1')
test_var_set_1.var_set("TEST_VAR_SET", "TEST_VAR_VALUE")

test_var_unset = Product('test_var_unset', '')
test_var_unset_1 = Package(test_var_unset, '1')
test_var_unset_1.var_unset("TEST_VAR_UNSET")

test_list_prepend = Product('test_list_prepend', '')
test_list_prepend_1 = Package(test_list_prepend, '1')
test_list_prepend_1.list_prepend("TEST_LIST_PREPEND", "TEST_LIST_PREPEND_ITEM")

test_list_append = Product('test_list_append', '')
test_list_append_1 = Package(test_list_append, '1')
test_list_append_1.list_append("TEST_LIST_APPEND", "TEST_LIST_APPEND_ITEM")

test_list_remove = Product('test_list_remove', '')
test_list_remove_1 = Package(test_list_remove, '1')
test_list_remove_1.list_remove("TEST_LIST_REMOVE", "TEST_LIST_REMOVE_ITEM")

test_path_prepend = Product('test_path_prepend', '')
test_path_prepend_1 = Package(test_path_prepend, '1')
test_path_prepend_1.path_prepend("TEST_PATH_PREPEND", "TEST_PATH_PREPEND_ITEM")

test_path_append = Product('test_path_append', '')
test_path_append_1 = Package(test_path_append, '1')
test_path_append_1.path_append("TEST_PATH_APPEND", "TEST_PATH_APPEND_ITEM")

test_path_remove = Product('test_path_remove', '')
test_path_remove_1 = Package(test_path_remove, '1')
test_path_remove_1.path_remove("TEST_PATH_REMOVE", "TEST_PATH_REMOVE_ITEM")

