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
import re


class Table(object):
    ALIGNMENTS = {
        'default': '',
        'd':       '',
        'left':    '<',
        'l':       '<',
        'center':  '^',
        'c':       '^',
        'right':   '>',
        'r':       '>',
    }
    def __init__(self,
            row_format,
            title=None,
            separator='',
            min_ordinal_length=3,
            max_row_length=70,
            show_header=True):
        self.max_row_length = max_row_length
        self.min_ordinal_length = min_ordinal_length
        self.show_header = show_header
        self.separator = separator
        self._columns = collections.OrderedDict()
        self._alignments = {}
        self._column_index = {}
        self._set_format(row_format)
        self.set_title(title)
        self._rows = []
        
    def _set_format(self, row_format):
        self._format = row_format
        r = re.compile(r'\{[^\{\}]+\}')
        self._formats = []
        gb = 0
        ge = 0
        b, e = 0, 0
        for match in r.finditer(row_format):
            b, e = match.span()
            if b > ge:
                self._formats.append((False, row_format[ge:b]))
            row_format_token = row_format[b:e]
            column = row_format_token[1:-1]
            self._columns[column] = column.upper()
            self._column_index[len(self._formats)] = column
            self._formats.append((True, row_format_token))
            gb = b
            ge = e
        last = row_format[e:]
        if last:
            self._formats.append((False, last))
        self._columns['__ordinal__'] = '#'
        self._alignments['__ordinal__'] = '>'

    @classmethod
    def format_title(self, title, max_row_length=70):
        if title is not None:
            title = "== {0} ".format(title)
            title += "=" * (max_row_length - len(title))
        return title

    def set_title(self, title=None):
        self._title = self.format_title(title, self.max_row_length)

    def set_column_title(self, **n_args):
        for column, title in n_args.items():
            #if not column in self._columns:
            #    raise KeyError("no such column {0!r}".format(column))
            self._columns[column] = title

    def set_column_alignment(self, **n_args):
        for column, align in n_args.items():
            alignment = self.ALIGNMENTS.get(align.lower(), None)
            if alignment is None:
                raise ValueError("no such alignment {0!r}".format(align))
            #if not column in self._columns:
            #    raise KeyError("no such column {0!r}".format(column))
            self._alignments[column] = alignment

    def make_row(self, row_index, **n_args):
        row = []
        for is_format, token in self._formats:
            if is_format:
                if '__ordinal__' in n_args:
                    row.append(token.format(**n_args))
                else:
                    row.append(token.format(__ordinal__=row_index, **n_args))
            else:
                row.append(token)
        return row

    def add_row(self, **n_args):
        self._rows.append(self.make_row(len(self._rows), **n_args))

    def add_rows(self, *rows):
        for row in rows:
            self.add_row(**row)

    def __iter__(self):
        if self._title:
            yield self._title
        table = []
        if self.show_header:
            table.append(self.make_row('', **self._columns))
        for row in self._rows:
            table.append(row)
        
        num_cols = len(self._formats)

        max_lengths = [max(len(row[col]) for row in table) for col in range(num_cols)]
        mods = []
        for index, max_length in enumerate(max_lengths[:-1]):
            column = self._column_index.get(index, None)
            alignment = self._alignments.get(column, '')
            if max_length:
                mods.append(":{0}{1}s".format(alignment, max_length))
            else:
                mods.append("")
        mods.append("")

        fmts = ["{{{i}{m}}}".format(i=i, m=m) for i, m in enumerate(mods)]
        fmt = self.separator.join(fmts)

        #l = max(len(str(len(table) - 1)), self.min_ordinal_length)
        #r_fmt = '{{0:{l}s}}) '.format(l=l) + fmt
        
        for row in table:
            #print(repr(fmt))
            #print(repr(row))
            yield fmt.format(*row)

    def render(self, printer_function=print):
        for line in self:
            print(line)
if __name__ == "__main__":
    t = Table('{__ordinal__}) {suite}:{package} {category} {tags}')

    l = [
        {'suite': 'intel', 'package': 'foo/0.3', 'category': 'library', 'tags': ''},
        {'suite': 'gnu',   'package': 'foo/0.3', 'category': 'library', 'tags': 'experimental'},
        {'suite': 'intel', 'package': 'foo/0.5', 'category': 'library', 'tags': 'good'},
        {'suite': 'intel', 'package': 'foo/0.56', 'category': 'library', 'tags': 'good'},
        {'suite': 'intel', 'package': 'foo/0.57', 'category': 'library', 'tags': 'good'},
        {'suite': 'intel', 'package': 'foo/0.58', 'category': 'library', 'tags': 'good'},
        {'suite': 'intel', 'package': 'foo/0.15', 'category': 'library', 'tags': 'good'},
        {'suite': 'intel', 'package': 'foo/0.34j5', 'category': 'library', 'tags': 'good'},
        {'suite': 'intel/12.1', 'package': 'foo/0.35', 'category': 'library', 'tags': 'good'},
        {'suite': 'intel', 'package': 'foo/0.0.05', 'category': 'library', 'tags': 'good'},
        {'suite': 'intel', 'package': 'foo/0', 'category': 'library', 'tags': 'good'},
        {'suite': 'intel', 'package': 'foofoo/0.5', 'category': 'library', 'tags': 'good'},
        {'suite': 'intel', 'package': 'foo/10.00.5', 'category': 'library', 'tags': 'good'},
    ]

    t.add_rows(*l)
    t.set_column_title(suite='XUITE')
    t.set_column_alignment(suite='center', package='right')

    print("-" * 70)
    t.render(print)
    print("-" * 70)

