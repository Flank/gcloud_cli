# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Tests that exercise the 'gcloud dns managed-zones list' command."""
from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util
from tests.lib.surface.dns import util_beta


class ManagedZonesListTest(base.DnsMockTest):

  def testZeroZonesList(self):
    self.mocked_dns_v1.managedZones.List.Expect(
        self.messages.DnsManagedZonesListRequest(
            project=self.Project(),
            maxResults=100),
        self.messages.ManagedZonesListResponse(managedZones=[]))

    self.Run('dns managed-zones list')
    self.AssertErrContains('Listed 0 items.')

  def testOneZoneList(self):
    self.mocked_dns_v1.managedZones.List.Expect(
        self.messages.DnsManagedZonesListRequest(
            project=self.Project(),
            maxResults=100),
        self.messages.ManagedZonesListResponse(
            managedZones=util.GetManagedZones()[:1]))

    self.Run('dns managed-zones list')
    self.AssertOutputContains("""\
NAME  DNS_NAME   DESCRIPTION
mz    zone.com.  My zone!
""", normalize_space=True)

  def testMultipleZonesList(self):
    self.mocked_dns_v1.managedZones.List.Expect(
        self.messages.DnsManagedZonesListRequest(
            project=self.Project(),
            maxResults=100),
        self.messages.ManagedZonesListResponse(
            managedZones=util.GetManagedZones()))

    self.Run('dns managed-zones list')
    self.AssertOutputContains("""\
NAME  DNS_NAME    DESCRIPTION
mz    zone.com.   My zone!
mz1   zone1.com.  My zone 1!
""", normalize_space=True)

  def testZonesListWithLimit(self):
    self.mocked_dns_v1.managedZones.List.Expect(
        self.messages.DnsManagedZonesListRequest(
            project=self.Project(),
            maxResults=1),
        self.messages.ManagedZonesListResponse(
            managedZones=util.GetManagedZones()))

    self.Run('dns managed-zones list --limit=1')
    self.AssertOutputContains("""\
NAME  DNS_NAME   DESCRIPTION
mz    zone.com.  My zone!
""", normalize_space=True)


class ManagedZonesListBetaTest(base.DnsMockBetaTest):

  def testMultipleZonesList(self):
    self.mocked_dns_client.managedZones.List.Expect(
        self.messages_beta.DnsManagedZonesListRequest(
            project=self.Project(),
            maxResults=100),
        self.messages_beta.ManagedZonesListResponse(
            managedZones=util_beta.GetManagedZones()))

    self.Run('dns managed-zones list')
    self.AssertOutputContains("""\
NAME  DNS_NAME    DESCRIPTION
mz    zone.com.   My zone!
mz1   zone1.com.  My zone 1!
""", normalize_space=True)


if __name__ == '__main__':
  test_case.main()
