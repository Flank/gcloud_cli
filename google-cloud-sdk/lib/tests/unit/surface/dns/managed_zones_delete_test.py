# -*- coding: utf-8 -*- #
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

"""Tests that exercise the 'gcloud dns managed-zones delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util
from tests.lib.surface.dns import util_beta


class ManagedZonesDeleteTest(base.DnsMockTest):

  def testDelete(self):
    test_zone = util.GetManagedZones()[0]
    self.mocked_dns_v1.managedZones.Delete.Expect(
        self.messages.DnsManagedZonesDeleteRequest(
            managedZone=test_zone.name,
            project=self.Project()),
        self.messages.DnsManagedZonesDeleteResponse())

    self.Run('dns managed-zones delete {0}'.format(test_zone.name))
    self.AssertOutputContains('')
    self.AssertErrContains("""\
Deleted [https://www.googleapis.com/dns/{0}/projects/{1}/managedZones/mz].
""".format(self.api_version, self.Project()))


class ManagedZonesDeleteBetaTest(base.DnsMockBetaTest):

  def testDelete(self):
    test_zone = util_beta.GetManagedZones()[0]
    self.mocked_dns_client.managedZones.Delete.Expect(
        self.messages_beta.DnsManagedZonesDeleteRequest(
            managedZone=test_zone.name,
            project=self.Project()),
        self.messages_beta.DnsManagedZonesDeleteResponse())

    self.Run('dns managed-zones delete {0}'.format(test_zone.name))
    self.AssertOutputContains('')
    self.AssertErrContains("""\
Deleted [https://www.googleapis.com/dns/{0}/projects/{1}/managedZones/mz].
""".format(self.api_version, self.Project()))


if __name__ == '__main__':
  test_case.main()
