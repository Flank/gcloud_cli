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
"""Tests for the allocations list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.compute import lister
from tests.lib.surface.compute import test_base
import mock


class AllocationsListAlphaTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('alpha')
    lister_patcher = mock.patch.object(
        lister, 'GetZonalResourcesDicts', autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_zonal_resources = lister_patcher.start()
    self.mock_get_zonal_resources.return_value = [
        self._MakeAllocation(
            'alloc1',
            'us-central1-iw1',
            3588257990483029726,
            '2018-09-16T19:23:45.219-07:00'),
        self._MakeAllocation(
            'alloc-10',
            'us-central1-broadwellir',
            8608544867917598655,
            '2018-09-05T12:41:04.544-07:00'),
        self._MakeAllocation(
            'alloc-20',
            'us-central1-broadwellir',
            7755358118601988876,
            '2018-09-13T20:07:15.703-07:00'),
    ]

  def testTableOutput(self):
    self.Run('alpha compute allocations list')
    self.mock_get_zonal_resources.assert_called()
    self.AssertOutputEquals(
        textwrap.dedent("""\
NAME      ZONE                     ID                   CREATION_TIMESTAMP
alloc1    us-central1-iw1          3588257990483029726  2018-09-16T19:23:45.219-07:00
alloc-10  us-central1-broadwellir  8608544867917598655  2018-09-05T12:41:04.544-07:00
alloc-20  us-central1-broadwellir  7755358118601988876  2018-09-13T20:07:15.703-07:00
            """),
        normalize_space=True)

  def _MakeAllocation(self, name, zone, alloc_id, creation_timestamp):
    return self.messages.Allocation(
        creationTimestamp=creation_timestamp,
        id=alloc_id,
        name=name,
        zone=zone)
