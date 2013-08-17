#!/usr/bin/env python3

#
# Copyright 2013 Simone Campagna
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

__author__ = 'Simone Campagna'

import collections

#def _print(d):
#    print("-" * 80)
#    for obj0, obj0_set in d.items():
#        print("{0} : {1}".format(obj0, ' '.join(str(obj1) for obj1 in obj0_set)))
#    print("-" * 80)

def sorted_dependencies(dependencies, objects=None, reverse=False):
    """sort_dependencies(dependencies, objects=None) -> list of sorted objects
dependencies: a dict with objects as keys, and sets of objects as values"""
    set_dependencies = collections.defaultdict(set)
    for obj, lst in dependencies.items():
        set_dependencies[obj] = set(lst)
    dependencies = set_dependencies
    if objects:
        for obj in objects:
            if not obj in dependencies:
                dependencies[obj] = set()
    all_objects = set()
    all_objects.update(dependencies.keys())
    for obj_set in dependencies.values():
        all_objects.update(obj_set)
    if objects is None:
        objects = all_objects
#    print("objects: ", objects)
#    print("all_objects: ", all_objects)
#    print("=== original:")
#    _print(dependencies)

    # complete dependencies:
#    i = -1
    while True:
#        i += 1
        changed = False
        for obj0 in list(dependencies.keys()):
            obj0_deps = dependencies[obj0]
            obj0_add_deps = set()
            for obj1 in obj0_deps:
                obj1_deps = dependencies[obj1]
                s = obj1_deps.difference(obj0_deps)
#                print(".", i, obj0, obj1, obj1_deps, s)
                if s:
                    obj0_add_deps.update(s)
            if obj0_add_deps:
#                print(">", i, obj0, obj0_add_deps, obj0_deps.union(obj0_add_deps))
                obj0_deps.update(obj0_add_deps)
                changed = True
        if not changed:
            break

#    print("=== after complete_dependencies:")
#    _print(dependencies)
#    input("...")

    # objects withot cycling dependencies:
    fixed_objects = set()
    cycling_objects = set()
    for obj in all_objects:
        if obj in dependencies[obj]:
            cycling_objects.add(obj)
        else:
            fixed_objects.add(obj)

#    print("=== fixed_objects:", fixed_objects)
#    print("=== cycling_objects:", cycling_objects)
#    input("...")
    
    dependency_level = {}
    # generating fixed dependencies:
    rem_objects = set(fixed_objects)
    while rem_objects:
        del_objects = set()
        for obj in rem_objects:
            if not dependencies[obj]:
                dependency_level.setdefault(obj, 0)
                del_objects.add(obj)
                for obj0 in rem_objects:
                    if obj in dependencies[obj0]:
                        dependencies[obj0].discard(obj)
                        dependency_level[obj0] = max(dependency_level.get(obj0, 0), dependency_level[obj] + 1)
        if del_objects:
            rem_objects.difference_update(del_objects)
        else:
            break

#    print("=== dependency_level:")
#    print("-" * 80)
#    for obj, level in dependency_level.items():
#        print("{0} : {1}".format(obj, level))
#    print("-" * 80)
#    input("---")
    
    for obj0 in cycling_objects:
        obj0_fixed_set = dependencies[obj0].intersection(fixed_objects)
        dependency_level[obj0] = max(dependency_level[obj1] for obj1 in obj0_fixed_set) + 1

    return sorted(objects, key=lambda obj: dependency_level[obj], reverse=reverse)


if __name__ == "__main__":
    import sys
    dependencies = {}
    for arg in sys.argv[1:]:
        key, deps_s = arg.split(':', 1)
        deps = deps_s.split(',')
        dependencies[key] = deps
    print(dependencies)
    sorted_objects = sort_dependencies(dependencies)
    print(sorted_objects)
