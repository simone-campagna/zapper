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
import textwrap

class Text(object):
    __re_split__ = re.compile(r'\n\n')
    def __init__(self, width=70):
        self.width = width

    def split_paragraphs(self, text):
        for paragraph in self.__re_split__.split(text):
            yield paragraph

    def wrap(self, text):
        lines = []
        for paragraph in self.split_paragraphs(text):
            lines.extend(self.wrap_paragraph(paragraph))
            lines.append('')
        return lines
       
    def wrap_paragraph(self, text):
        return textwrap.wrap(textwrap.dedent(text), width=self.width)

    def fill(self, text):
        return '\n'.join(self.wrap(text))

if __name__ == "__main__":
    text = """\
This is a very long long long line, and it should be splitted in several lines, each of them not longer than 70 characters. This will be the first paragraph.
This line belongs to the same first paragraph.

This line belongs to the second paragraph, and not to the first one. Indeed two newlines are used to separate it from the first one.
This is the second paragraph too.

This is the last paragraph. It is an useless line, as the ones above, but it is a useful example.
This is the last line of the last paragraph."""

    t = Text()
    print(t.fill(text))
