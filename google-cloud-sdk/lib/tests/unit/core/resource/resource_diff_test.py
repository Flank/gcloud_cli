# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Unit tests for the resource_diff module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_diff
from tests.lib.core.resource import resource_printer_test_base


class ResourceDiffTest(resource_printer_test_base.Base):

  def testResourceDiff(self):
    original = 'one\ntwo\ntree\nfour\nfive\n'
    changed = 'one\ntwo\nthree\nfour\nfive\n'
    diff = resource_diff.ResourceDiff(original, changed)
    diff.Print('flattened')
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


if __name__ == '__main__':
  resource_printer_test_base.main()
