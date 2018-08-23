# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for the diff_printer module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_printer
from tests.lib.core.resource import resource_printer_test_base


class DiffPrinterTest(resource_printer_test_base.Base):

  def testResourceDiffLines(self):
    resource = {
        'old': 'one\ntwo\ntree\nfour\nfive\n',
        'new': 'one\ntwo\nthree\nfour\nfive\n',
    }
    resource_printer.Print(resource, 'diff(old, new)')
    self.AssertOutputEquals(
        '--- \n'
        '\n'
        '+++ \n'
        '\n'
        '@@ -1,2 +1,2 @@\n'
        '\n'
        '-: "one\\ntwo\\ntree\\nfour\\nfive\\n"\n'
        '+: "one\\ntwo\\nthree\\nfour\\nfive\\n"\n'
        ' \n',
        normalize_space=True)

  def testResourceDiffList(self):
    resource = {
        'old': ['one', 'two', 'tree', 'four', 'five'],
        'new': ['one', 'two', 'three', 'four', 'five'],
    }
    resource_printer.Print(resource, 'diff(old, new)')
    self.AssertOutputEquals("""\
---

+++

@@ -1,6 +1,6 @@

[0]: one
[1]: two
-[2]: tree
+[2]: three
[3]: four
[4]: five

""",
                            normalize_space=True)

  def testResourceDiffListYaml(self):
    resource = {
        'old': ['one', 'two', 'tree', 'four', 'five'],
        'new': ['one', 'two', 'three', 'four', 'five'],
    }
    resource_printer.Print(resource, 'diff[format=yaml](old, new)')
    self.AssertOutputEquals("""\
---

+++

@@ -1,6 +1,6 @@

- one
- two
-- tree
+- three
- four
- five

""",
                            normalize_space=True)

  def testResourceDiffListJsonWithTitle(self):
    resource = {
        'old': ['one', 'two', 'tree', 'four', 'five'],
        'new': ['one', 'two', 'three', 'four', 'five'],
    }
    resource_printer.Print(
        resource, 'diff[format=json,title="JSON diff"](old, new)')
    self.AssertOutputEquals("""\
JSON diff
---

+++

@@ -1,7 +1,7 @@

[
"one",
"two",
- "tree",
+ "three",
"four",
"five"
]
""",
                            normalize_space=True)

  def testResourceDiffListOldOnly(self):
    resource = {
        'old': ['one', 'two', 'tree', 'four', 'five'],
    }
    resource_printer.Print(
        resource, 'diff(old, new)')
    self.AssertOutputEquals("""\
---

+++

@@ -1,6 +1,2 @@

-[0]: one
-[1]: two
-[2]: tree
-[3]: four
-[4]: five
+: None

""",
                            normalize_space=True)

  def testResourceDiffListNewOnly(self):
    resource = {
        'new': ['one', 'two', 'three', 'four', 'five'],
    }
    resource_printer.Print(
        resource, 'diff(old, new)')
    self.AssertOutputEquals("""\
---

+++

@@ -1,2 +1,6 @@

-: None
+[0]: one
+[1]: two
+[2]: three
+[3]: four
+[4]: five

""",
                            normalize_space=True)

  def testResourceDiffListEmpty(self):
    resource = {
        'foo': ['one', 'two', 'tree', 'four', 'five'],
        'bar': ['one', 'two', 'three', 'four', 'five'],
    }
    resource_printer.Print(
        resource, 'diff(old, new)')
    self.AssertOutputEquals("""\
""",
                            normalize_space=True)


if __name__ == '__main__':
  resource_printer_test_base.main()
