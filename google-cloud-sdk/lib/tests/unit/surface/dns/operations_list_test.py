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

from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util_beta


class OperationsListBetaTest(base.DnsMockBetaTest):

  def testZoneZeroOperationsList(self):
    messages = self.messages_beta
    self.mocked_dns_client.managedZoneOperations.List.Expect(
        messages.DnsManagedZoneOperationsListRequest(project=self.Project(),
                                                     maxResults=100,
                                                     managedZone=u'my-zone'),
        messages.ManagedZoneOperationsListResponse(operations=[]))
    self.Run('dns operations list --zones my-zone')
    self.AssertErrContains('Listed 0 items.')

  def testZoneMultipleOperationsList(self):
    messages = self.messages_beta
    test_zones = util_beta.GetManagedZones()
    self.mocked_dns_client.managedZoneOperations.List.Expect(
        messages.DnsManagedZoneOperationsListRequest(project=self.Project(),
                                                     maxResults=100,
                                                     managedZone=u'my-zone'),
        messages.ManagedZoneOperationsListResponse(operations=[
            messages.Operation(
                id='1',
                startTime='2015-10-02T15:00:00Z',
                user='cloud-dns-system',
                zoneContext=messages.OperationManagedZoneContext(
                    oldValue=test_zones[0],
                    newValue=test_zones[0]),
                type='update',),
            messages.Operation(
                id='2',
                startTime='2015-10-05T15:00:00Z',
                user='example@google.com',
                zoneContext=messages.OperationManagedZoneContext(
                    oldValue=test_zones[1],
                    newValue=test_zones[1]),
                type='delete',),
        ]))
    self.Run('dns operations list --zones my-zone')
    self.AssertOutputContains("""\
ZONE_NAME ID START_TIME           USER               TYPE
mz        1  2015-10-02T15:00:00Z cloud-dns-system   update
mz1       2  2015-10-05T15:00:00Z example@google.com delete
""", normalize_space=True)


if __name__ == '__main__':
  test_case.main()
