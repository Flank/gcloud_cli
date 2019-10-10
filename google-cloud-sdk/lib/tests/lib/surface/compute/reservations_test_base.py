# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Base class for compute reservations tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import sdk_test_base
from tests.lib.surface.compute import test_base


class TestBase(sdk_test_base.WithFakeAuth, test_base.BaseTest):
  """Base class for compute reservations unit tests."""

  def SetUpTrack(self, track):
    if track == calliope_base.ReleaseTrack.ALPHA:
      self.api_version = 'alpha'
    elif track == calliope_base.ReleaseTrack.BETA:
      self.api_version = 'beta'
    else:
      self.api_version = 'v1'
    self.SelectApi(self.api_version)
    self.mock_client = mock.Client(
        apis.GetClientClass('compute', self.api_version),
        real_client=apis.GetClientInstance(
            'compute', self.api_version, no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def SetUp(self):
    self.SetUpTrack(self.track)

  def _MakeSpecificSKUReservation(self, name, zone='us-central1-a', count=1):
    return self.messages.Reservation(
        name=name,
        zone=zone,
        specificReservation=self.messages.AllocationSpecificSKUReservation(
            count=count, inUseCount=0))
