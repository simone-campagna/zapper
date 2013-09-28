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

import re
import string
import collections

from .debug import PRINT

class _FormatSpecData(object):
    KEYS = ('fill', 'align', 'sign', 'alternate', 'zero', 'width', 'comma', 'precision', 'type')
    #RE_FORMAT_SPEC = re.compile(r"(?P<fill>[^\{\}])?(?P<align>[\<\>\=\^])?(?P<sign>[\+\- ])?(?P<alternate>\#)?(?P<zero>0)?(?P<width>[1-9]+\d*)?(?P<comma>,)?(?P<precision>.\d+)?(?P<type>[sbcdoxXneEfFgG\%])?")
    RE_FORMAT_SPEC = re.compile(r"(?P<align>[\<\>\=\^])?(?P<sign>[\+\- ])?(?P<alternate>\#)?(?P<zero>0)?(?P<width>[1-9]+\d*)?(?P<comma>,)?(?P<precision>.\d+)?(?P<type>[sbcdoxXneEfFgG\%])?")
    def __init__(self, fspec):
        if fspec is None:
            fspec = ''
        if isinstance(fspec, _FormatSpecData):
            for key in self.KEYS:
                setattr(self, key, getattr(fspec, key))
        elif isinstance(fspec, str):
            m = self.RE_FORMAT_SPEC.search(fspec)
            if not m:
                raise ValueError("invalid format spec {0!r}".format(fspec))
            b, e = m.span()
            if b == 0:
                fill = None
            else:
                fill = fspec[:b]
            self.fill = fill
            for key, val in m.groupdict().items():
                #print("... {}={!r}".format(key, val))
                setattr(self, key, val)
        else:
            raise TypeError("unsupported type {0}".format(type(fspec).__name__))
    
    def __str__(self):
        l = []
        for key in self.KEYS:
            val = getattr(self, key)
            #print("KEY {0}={1!r}".format(key, val))
            if val is not None:
                l.append(str(val))
        return ''.join(l)

    def copy(self):
        return self.__class__(str(self))

class Table(object):
    _FormatItem = collections.namedtuple('_FormatItem', ('pre', 'name', 'format_spec', 'conversion', 'format_spec_data'))
    def __init__(self,
            row_format,
            title=None,
            separator='',
            min_ordinal_length=3,
            max_row_length=70,
            show_header=True,
            show_header_if_empty=True):
        self.max_row_length = max_row_length
        self.min_ordinal_length = min_ordinal_length
        self.show_header = show_header
        self.show_header_if_empty = show_header_if_empty
        self.separator = separator
        self._columns = collections.OrderedDict()
        self._set_format(row_format)
        self.set_title(title)
        self._rows = []
        
    def columns(self):
        return iter(self._columns)

    def _set_format(self, row_format):
        formatter = string.Formatter()
        next_positional = 0
        self._format_items = []
        self._body_formats = []
        self._header_formats = []
        self._num_cols = 0
        for pre, name, format_spec, conversion in formatter.parse(row_format):
            self._num_cols += 1
            is_format = True
            fill = None
            width = None
            align = None
            if name is None:
                is_format = False
            else:
                is_format = True
                self._num_cols += 1
                if name:
                    try:
                        iname = int(name)
                        name = iname
                        next_positional = name
                    except ValueError as e:
                        pass
                else:
                    name = next_positional
                    next_positional += 1
            format_spec_data = _FormatSpecData(format_spec)
            format_item = self._FormatItem(
                pre=pre, 
                name=name, 
                format_spec=format_spec, 
                conversion=conversion,
                format_spec_data=format_spec_data)
            self._format_items.append(format_item)
            if name is not None:
                self._columns[name] = str(name).upper()
            if is_format:
                align = format_spec_data.align
                header_format_spec_data = format_spec_data.copy()
                header_format_spec_data.precision = None
                header_format_spec_data.type = 's'
                header_format_spec_data.sign = None
                header_format_spec_data.alternate = None
                header_format_spec_data.fill = None
                header_format_spec_data.zero = None
                if header_format_spec_data.align == '=':
                    header_format_spec_data.align = '<'
                header_format_spec = str(header_format_spec_data)
                if conversion is None:
                    conversion = ''
                if conversion:
                    conversion = '!' + conversion
                if format_spec:
                    format_spec = ':' + format_spec
                if header_format_spec:
                    header_format_spec = ':' + header_format_spec
                body_fmt = '{{{0}{1}{2}}}'.format(name, conversion, format_spec)
                header_fmt = '{{{0}{1}}}'.format(name, header_format_spec)
                self._body_formats.append(body_fmt)
                self._header_formats.append(header_fmt)
            else:
                self._body_formats.append("")
                self._header_formats.append("")
        self._columns['__ordinal__'] = '#'
                

    @classmethod
    def format_title(self, title, max_row_length=70):
        if title is not None:
            title = "== {0} ".format(title)
            title += "=" * (max_row_length - len(title))
        return title

    def set_title(self, title=None):
        self._title = self.format_title(title, self.max_row_length)

    def set_column_title(self, *p_args, **n_args):
        for column, title in enumerate(p_args):
            self._columns[column] = title
        for column, title in n_args.items():
            #if not column in self._columns:
            #    raise KeyError("no such column {0!r}".format(column))
            self._columns[column] = title

    def _make_row(self, is_header, row_index, *p_args, **n_args):
        row = []
        for format_index, format_item in enumerate(self._format_items):
            row.append(format_item.pre)
            name = format_item.name
            if name is None:
                col = ''
            else:
                if is_header:
                    fmt = self._header_formats[format_index]
                else:
                    fmt = self._body_formats[format_index]
                if not '__ordinal__' in n_args:
                    n_args['__ordinal__'] = row_index
                col = fmt.format(*p_args, **n_args)
                #print(is_header, repr(fmt), p_args, n_args, '---> {0!r}'.format(col))
            row.append(col)
        return row

    def _make_body_row(self, row_index, *p_args, **n_args):
        return self._make_row(False, row_index, *p_args, **n_args)

    def _make_header_row(self, row_index, *p_args, **n_args):
        #print(row_index, p_args, n_args)
        return self._make_row(True, row_index, *p_args, **n_args)

    def _make_header(self):
        p_args = []
        n_args = {}
        for key, val in self._columns.items():
            if isinstance(key, str):
                n_args[key] = val
            else:
                p_args.append(val)
        return self._make_header_row('', *p_args, **n_args)

    def add_row(self, *p_args, **n_args):
        self._rows.append(self._make_body_row(len(self._rows), *p_args, **n_args))

    def add_header_row(self, *p_args, **n_args):
        self._rows.append(self._make_header_row(len(self._rows), *p_args, **n_args))

    def __iter__(self):
        if self._title:
            yield self._title
        table = []
        if self.show_header_if_empty or (self.show_header and self._rows):
            table.append(self._make_header())
        for row in self._rows:
            table.append(row)
        
        if len(table) == 0:
            return 

        num_cols = self._num_cols

        max_lengths = [max(len(row[col]) for row in table) for col in range(num_cols)]

        #print(max_lengths)
        aligns = []
        for format_item in self._format_items:
            aligns.append('<') # for pre
            format_spec_data = format_item.format_spec_data
            align = format_spec_data.align
            if align == '=':
                align = '<'
            aligns.append(align)
        #print(aligns)

        mods = []
        for max_length, align in zip(max_lengths[:-1], aligns[:-1]):
            if align is None:
                align = '<'
            if max_length:
                mods.append(":{0}{1}s".format(align, max_length))
            else:
                mods.append("")
        if max_lengths:
            align, max_length = aligns[-1], max_lengths[-1]
            if (align is None or align == '<') or max_length == 0:
                mods.append("")
            else:
                mods.append(":{0}{1}s".format(align, max_length))

        fmts = ["{{{i}{m}}}".format(i=i, m=m) for i, m in enumerate(mods)]
        fmt = self.separator.join(fmts)
        #print(mods)
        #print(fmt)

        #l = max(len(str(len(table) - 1)), self.min_ordinal_length)
        #r_fmt = '{{0:{l}s}}) '.format(l=l) + fmt
        
        for row in table:
            #print(repr(fmt))
            #print(repr(row))
            yield fmt.format(*row)

    def render(self, printer_function=None):
        if printer_function is None:
            printer_function = PRINT
        for line in self:
            printer_function(line)

def show_table(title, lst, printer_function=None):
    if printer_function is None:
        printer_function = PRINT
    lst = tuple(lst)
    if lst:
        if isinstance(lst[0], (tuple, list)):
            lst = tuple(tuple(str(e) for e in row) for row in lst)
        else:
            lst = tuple((str(e), ) for e in lst)
        l = len(lst[0])
        fmt = "{__ordinal__:>3d}) " + ' '.join("{}" for i in range(l))
        t = Table(fmt, title=title, show_header=False)
        for row in lst:
            t.add_row(*row)
        t.render(printer_function)

def show_title(title, printer_function=None):
    if printer_function is None:
        printer_function = PRINT
    printer_function(Table.format_title(title))

def validate_format(fmt, *p_args, **n_args):
    t = Table(fmt)
    for column in t.columns():
        if isinstance(column, int):
            if column >= len(p_args):
                raise KeyError("format {0!r}: no such column {1!r}".format(fmt, column))
        else:
            if not column in n_args:
                raise KeyError("format {0!r}: no such column {1!r}".format(fmt, column))

if __name__ == "__main__":
    lt = [
        ('intel', 'foo/0.3', 'library', ''),
        ('gnu',   'foo/0.3', 'library', 'experimental very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very long'),
        ('intel', 'foo/0.5', 'library', 'good'),
        ('intel', 'foo/0.56', 'library', 'good'),
        ('intel', 'foo/0.57', 'library', 'good'),
        ('intel', 'foo/0.58', 'library', 'good_but_not_perfect'),
        ('intel', 'foo/0.15', 'library', 'good'),
        ('intel', 'foo/0.34j5', 'library', 'good'),
        ('intel/12.1', 'foo/0.35', 'library', 'good'),
        ('intel', 'foo/0.0.05', 'library', 'good'),
        ('intel', 'foo/0', 'library', 'good'),
        ('intel', 'foofoo/0.5', 'library', 'good'),
        ('intel', 'foo/10.00.5', 'library', 'good'),
    ]

    keys = ['suite', 'package', 'category', 'tags']

    ld = [dict(zip(keys, t)) for t in lt]
#        {'suite': 'intel', 'package': 'foo/0.3', 'category': 'library', 'tags': ''},
#        {'suite': 'gnu',   'package': 'foo/0.3', 'category': 'library', 'tags': 'experimental very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very long'},
#        {'suite': 'intel', 'package': 'foo/0.5', 'category': 'library', 'tags': 'good'},
#        {'suite': 'intel', 'package': 'foo/0.56', 'category': 'library', 'tags': 'good'},
#        {'suite': 'intel', 'package': 'foo/0.57', 'category': 'library', 'tags': 'good'},
#        {'suite': 'intel', 'package': 'foo/0.58', 'category': 'library', 'tags': 'good_but_not_perfect'},
#        {'suite': 'intel', 'package': 'foo/0.15', 'category': 'library', 'tags': 'good'},
#        {'suite': 'intel', 'package': 'foo/0.34j5', 'category': 'library', 'tags': 'good'},
#        {'suite': 'intel/12.1', 'package': 'foo/0.35', 'category': 'library', 'tags': 'good'},
#        {'suite': 'intel', 'package': 'foo/0.0.05', 'category': 'library', 'tags': 'good'},
#        {'suite': 'intel', 'package': 'foo/0', 'category': 'library', 'tags': 'good'},
#        {'suite': 'intel', 'package': 'foofoo/0.5', 'category': 'library', 'tags': 'good'},
#        {'suite': 'intel', 'package': 'foo/10.00.5', 'category': 'library', 'tags': 'good'},
#    ]

    t1 = Table('{__ordinal__:>+#3d}) {suite!r:^20s}:{package:>s} {category} {tags:<}')
    t1.set_column_title(suite='XUITE')
    t2 = Table('{__ordinal__:>+#3d}) {!r:^20s}:{:>s} {} {:<}')
    t2.set_column_title(*[k.upper() for k in keys])

    for i, (l, t) in enumerate(((ld, t1), (lt, t2))):
        for row in l:
            if isinstance(row, collections.Mapping):
                t.add_row(**row)
            else:
                t.add_row(*row)

    
        print("-" * 70)
        t.render(print)
        print("-" * 70)
        input("t{0} done...".format(i))


