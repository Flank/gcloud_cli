# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests for command_lib.projects.util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.command_lib.projects import util
from tests.lib import subtests
from tests.lib import test_case


class IdsFromNameTest(subtests.Base):

  def RunSubTest(self, name, id_expression):  # pylint: disable=arguments-differ
    val = util.IdFromName(name)
    self.assertTrue(re.match(id_expression, val),
                    msg="'{}' does not match '{}'".format(id_expression, val))

  def testMatches(self):
    suggestions = [
        ('a', r'a-\d{6}'),  # short
        ('abcdefghijklmnopqrstuvwxyzabcd',
         'abcdefghijklmnopqrstuvwxyzabcd'),  # long uses no magic number
        ('FooBaR', r'foobar-\d{6}'),  # case
        ('A b/c.d_e\tf-g', r'a-b-c-d-e-f-g-\d{6}'),  # spaces
        ('a?b^c$d(e)', r'abcde-\d{6}'),  # weird ascii
        ('ab-123-c5d', r'ab-123-c5d-\d{6}'),  # digits
        ('a\U0001f489b', r'ab-\d{6}'),  # unicode
        ('123abcdefghijklmnopqrstuvwxyz456',
         'abcdefghijklmnopqrstuvwxyz456'),  # leading digits
        ('abc_-  /def', r'abc-def-\d{6}'),  # consolidate spaces
        ('-abcdefghijklmnopqrstuvwxyz-',
         'abcdefghijklmnopqrstuvwxyz')  # leading and trailing spaces
    ]
    for (name, id_exp) in suggestions:
      self.Run(None, name, id_exp)


if __name__ == '__main__':
  test_case.main()
