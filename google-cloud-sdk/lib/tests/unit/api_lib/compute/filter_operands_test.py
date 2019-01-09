# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Unit tests for the filter_operands module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import filter_operands
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.parameterized_line_no import LineNo as T


class GetFilterOperandsTest(parameterized.TestCase):

  # Notice: We expect the :(... AND ...) tests to fail when all the filter
  # implementations agree on :(...) scoped expressions. When that is fixed the
  # affected tests should be changed to return None. The filter_operands
  # module is already coded to handle that change.

  @parameterized.parameters(
      T(None,
        None,
        None),
      T('',
        None,
        None),

      T('(zone:(my-zone-1 my-zone-2))',
        {'zone'},
        {'my-zone-1', 'my-zone-2'}),
      T('(zone:(my-zone-1 OR my-zone-2))',
        {'zone'},
        {'my-zone-1', 'my-zone-2'}),
      T('(zone:(my-zone-1 AND my-zone-2))',
        {'zone'},
        {'my-zone-1', 'my-zone-2'}),
      T('(zone:(my-zone-1 my-zone-2) OR name:*)',
        {'zone'},
        None),
      T('(zone:(my-zone-1 OR my-zone-2) OR name:*)',
        {'zone'},
        None),
      T('(zone:(my-zone-1 AND my-zone-2) OR name:*)',
        {'zone'},
        None),
      T('(zone:(my-zone-1 my-zone-2) AND name:*)',
        {'zone'},
        {'my-zone-1', 'my-zone-2'}),
      T('(zone:(my-zone-1 OR my-zone-2) AND name:*)',
        {'zone'},
        {'my-zone-1', 'my-zone-2'}),
      T('(zone:(my-zone-1 AND my-zone-2) AND name:*)',
        {'zone'},
        {'my-zone-1', 'my-zone-2'}),

      T('(zones:(my-zone-1 my-zone-2))',
        {'zones'},
        {'my-zone-1', 'my-zone-2'}),
      T('(zones:(my-zone-1 OR my-zone-2))',
        {'zones'},
        {'my-zone-1', 'my-zone-2'}),
      T('(zones:(my-zone-1 AND my-zone-2))',
        {'zones'},
        {'my-zone-1', 'my-zone-2'}),
      T('(zones:(my-zone-1 my-zone-2) OR name:*)',
        {'zones'},
        None),
      T('(zones:(my-zone-1 OR my-zone-2) OR name:*)',
        {'zones'},
        None),
      T('(zones:(my-zone-1 AND my-zone-2) OR name:*)',
        {'zones'},
        None),
      T('(zones:(my-zone-1 my-zone-2) AND name:*)',
        {'zones'},
        {'my-zone-1', 'my-zone-2'}),
      T('(zones:(my-zone-1 OR my-zone-2) AND name:*)',
        {'zones'},
        {'my-zone-1', 'my-zone-2'}),
      T('(zones:(my-zone-1 AND my-zone-2) AND name:*)',
        {'zones'},
        {'my-zone-1', 'my-zone-2'}),

      T('zone:(my-zone-1 OR my-zone-2) '
        'zones:(my-zone-3 OR my-zone-4)',
        {'zone', 'zones'},
        {'my-zone-1', 'my-zone-2', 'my-zone-3', 'my-zone-4'}),

      T('(region:(my-region-1 my-region-2))',
        {'region'},
        {'my-region-1', 'my-region-2'}),
      T('(region:(my-region-1 OR my-region-2))',
        {'region'},
        {'my-region-1', 'my-region-2'}),
      T('(region:(my-region-1 AND my-region-2))',
        {'region'},
        {'my-region-1', 'my-region-2'}),
      T('(region:(my-region-1 my-region-2) OR name:*)',
        {'region'},
        None),
      T('(region:(my-region-1 OR my-region-2) OR name:*)',
        {'region'},
        None),
      T('(region:(my-region-1 AND my-region-2) OR name:*)',
        {'region'},
        None),
      T('(region:(my-region-1 my-region-2) AND name:*)',
        {'region'},
        {'my-region-1', 'my-region-2'}),
      T('(region:(my-region-1 OR my-region-2) AND name:*)',
        {'region'},
        {'my-region-1', 'my-region-2'}),
      T('(region:(my-region-1 AND my-region-2) AND name:*)',
        {'region'},
        {'my-region-1', 'my-region-2'}),

      T('(regions:(my-region-1 my-region-2))',
        {'regions'},
        {'my-region-1', 'my-region-2'}),
      T('(regions:(my-region-1 OR my-region-2))',
        {'regions'},
        {'my-region-1', 'my-region-2'}),
      T('(regions:(my-region-1 AND my-region-2))',
        {'regions'},
        {'my-region-1', 'my-region-2'}),
      T('(regions:(my-region-1 my-region-2) OR name:*)',
        {'regions'},
        None),
      T('(regions:(my-region-1 OR my-region-2) OR name:*)',
        {'regions'},
        None),
      T('(regions:(my-region-1 AND my-region-2) OR name:*)',
        {'regions'},
        None),
      T('(regions:(my-region-1 my-region-2) AND name:*)',
        {'regions'},
        {'my-region-1', 'my-region-2'}),
      T('(regions:(my-region-1 OR my-region-2) AND name:*)',
        {'regions'},
        {'my-region-1', 'my-region-2'}),
      T('(regions:(my-region-1 AND my-region-2) AND name:*)',
        {'regions'},
        {'my-region-1', 'my-region-2'}),

      T('region:(my-region-1 OR my-region-2) '
        'regions:(my-region-3 OR my-region-4)',
        {'region', 'regions'},
        {'my-region-1', 'my-region-2', 'my-region-3', 'my-region-4'}),
  )
  def testGetFilterOperands(self, line, expression, keys, expected):
    _, actual = filter_operands.GetFilterOperands().Rewrite(
        expression, keys=keys)
    self.assertEqual(expected, actual)


if __name__ == '__main__':
  test_case.main()
