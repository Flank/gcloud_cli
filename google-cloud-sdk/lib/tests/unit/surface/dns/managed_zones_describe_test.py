# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Tests that exercise the 'gcloud dns managed-zones describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util
from tests.lib.surface.dns import util_beta


class ManagedZonesDescribeTest(base.DnsMockTest):

  def testDescribe(self):
    test_zone = util.GetManagedZones()[0]
    self.mocked_dns_v1.managedZones.Get.Expect(
        self.messages.DnsManagedZonesGetRequest(
            managedZone=test_zone.name,
            project=self.Project()),
        test_zone)

    result = self.Run('dns managed-zones describe {0}'.format(test_zone.name))
    self.assertEqual(test_zone, result)

    self.AssertOutputContains("""\
creationTime: '2014-10-20T20:06:50.077Z'
description: My zone!
dnsName: zone.com.
id: '67371891'
kind: dns#managedZone
name: mz
nameServers:
- ns-cloud-e1.googledomains.com.
- ns-cloud-e2.googledomains.com.
- ns-cloud-e3.googledomains.com.
- ns-cloud-e4.googledomains.com.
""", normalize_space=True)


class ManagedZonesDescribeBetaTest(base.DnsMockBetaTest):

  def testDescribe(self):
    test_zone = util_beta.GetManagedZones()[0]
    self.mocked_dns_client.managedZones.Get.Expect(
        self.messages_beta.DnsManagedZonesGetRequest(
            managedZone=test_zone.name,
            project=self.Project()),
        test_zone)

    result = self.Run('dns managed-zones describe {0}'.format(test_zone.name))
    self.assertEqual(test_zone, result)

    self.AssertOutputContains("""\
creationTime: '2014-10-20T20:06:50.077Z'
description: My zone!
dnsName: zone.com.
id: '67371891'
kind: dns#managedZone
name: mz
nameServers:
- ns-cloud-e1.googledomains.com.
- ns-cloud-e2.googledomains.com.
- ns-cloud-e3.googledomains.com.
- ns-cloud-e4.googledomains.com.
""", normalize_space=True)


if __name__ == '__main__':
  test_case.main()
