# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for the reservations list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import reservations_test_base as test_base

import mock


class ListTest(test_base.TestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.SelectApi('v1')
    lister_patcher = mock.patch.object(
        lister, 'GetZonalResourcesDicts', autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_zonal_resources = lister_patcher.start()
    self.mock_get_zonal_resources.return_value = [
        self._MakeSpecificSKUReservation('alloc-1'),
        self._MakeSpecificSKUReservation('alloc-2'),
        self._MakeSpecificSKUReservation('alloc-3'),
    ]

  def testTableOutput(self):
    self.Run('compute reservations list')
    self.mock_get_zonal_resources.assert_called()
    self.AssertOutputEquals(
        textwrap.dedent("""\
NAME IN_USE_COUNT COUNT ZONE
alloc-1 0 1 us-central1-a
alloc-2 0 1 us-central1-a
alloc-3 0 1 us-central1-a
            """),
        normalize_space=True)


class ListTestBeta(ListTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.SelectApi('beta')


class ListTestAlpha(ListTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.SelectApi('alpha')


if __name__ == '__main__':
  test_case.main()
