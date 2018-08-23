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
"""Tests for the regions list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.core.resource import resource_projector
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock


class RegionsListTest(test_base.BaseTest):

  def SetUp(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(test_resources.REGIONS))

  def testTabularOutput(self):
    self.Run("""
        compute regions list
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute_v1.regions,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
NAME      CPUS       DISKS_GB    ADDRESSES  RESERVED_ADDRESSES STATUS           TURNDOWN_DATE
region-1  0/24       30/5120     2/24       1/7                UP (DEPRECATED)  2015-03-29T00:00:00.000-07:00
region-2  0/240      300/51200   20/240     10/70              UP
region-3  2000/4800  600/102400  40/480     20/140             UP
            """), normalize_space=True)


if __name__ == '__main__':
  test_case.main()
