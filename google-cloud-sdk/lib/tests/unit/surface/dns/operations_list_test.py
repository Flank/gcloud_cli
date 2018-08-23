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
"""Tests that exercise the 'gcloud dns operations list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util


@parameterized.named_parameters(
    ('Beta', calliope_base.ReleaseTrack.BETA, 'v1beta2'),
    ('GA', calliope_base.ReleaseTrack.GA, 'v1'),
)
class OperationsListTest(base.DnsMockMultiTrackTest):

  def testZoneZeroOperationsList(self, track, api_version):
    self.SetUpForTrack(track, api_version)
    messages = self.messages
    self.client.managedZoneOperations.List.Expect(
        messages.DnsManagedZoneOperationsListRequest(project=self.Project(),
                                                     maxResults=100,
                                                     managedZone='my-zone'),
        messages.ManagedZoneOperationsListResponse(operations=[]))
    self.Run('dns operations list --zones my-zone')
    self.AssertErrContains('Listed 0 items.')

  def testZoneMultipleOperationsList(self, track, api_version):
    self.SetUpForTrack(track, api_version)
    messages = self.messages
    test_zones = util.GetManagedZones(api_version)
    self.client.managedZoneOperations.List.Expect(
        messages.DnsManagedZoneOperationsListRequest(project=self.Project(),
                                                     maxResults=100,
                                                     managedZone='mz'),
        messages.ManagedZoneOperationsListResponse(operations=[
            messages.Operation(
                id='1',
                startTime='2015-10-02T15:00:00Z',
                user='cloud-dns-system',
                zoneContext=messages.OperationManagedZoneContext(
                    oldValue=test_zones[0],
                    newValue=test_zones[0]),
                type='update',),
        ]))
    self.client.managedZoneOperations.List.Expect(
        messages.DnsManagedZoneOperationsListRequest(project=self.Project(),
                                                     maxResults=100,
                                                     managedZone='mz1'),
        messages.ManagedZoneOperationsListResponse(operations=[
            messages.Operation(
                id='2',
                startTime='2015-10-05T15:00:00Z',
                user='example@google.com',
                zoneContext=messages.OperationManagedZoneContext(
                    oldValue=test_zones[1],
                    newValue=test_zones[1]),
                type='delete',),
        ]))
    self.Run('dns operations list --zones mz,mz1')
    self.AssertOutputContains("""\
ZONE_NAME ID START_TIME           USER               TYPE
mz        1  2015-10-02T15:00:00Z cloud-dns-system   update
mz1       2  2015-10-05T15:00:00Z example@google.com delete
""", normalize_space=True)


if __name__ == '__main__':
  test_case.main()
