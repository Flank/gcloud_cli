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

"""Tests that exercise the 'gcloud dns project-info describe' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.surface.dns import base


class ProjectInfoDescribeTest(base.DnsMockTest):

  def testDescribe(self):
    test_project = self.messages.Project(
        id=self.Project(),
        kind='dns#project',
        number=1234567,
        quota=self.messages.Quota(
            kind='dns#quota',
            managedZones=100,
            resourceRecordsPerRrset=20,
            rrsetAdditionsPerChange=100,
            rrsetDeletionsPerChange=100,
            rrsetsPerManagedZone=10000,
            totalRrdataSizePerChange=10000,
        ))
    self.mocked_dns_v1.projects.Get.Expect(
        self.messages.DnsProjectsGetRequest(project=test_project.id),
        test_project)

    result = self.Run('dns project-info describe {0}'.format(test_project.id))
    self.assertEqual(test_project, result)

    self.AssertOutputContains("""\
id: fake-project
kind: dns#project
number: '1234567'
quota:
  kind: dns#quota
  managedZones: 100
  resourceRecordsPerRrset: 20
  rrsetAdditionsPerChange: 100
  rrsetDeletionsPerChange: 100
  rrsetsPerManagedZone: 10000
  totalRrdataSizePerChange: 10000
""", normalize_space=True)


class ProjectInfoDescribeBetaTest(base.DnsMockBetaTest):

  def testDescribe(self):
    test_project = self.messages_beta.Project(
        id=self.Project(),
        kind='dns#project',
        number=1234567,
        quota=self.messages_beta.Quota(
            kind='dns#quota',
            managedZones=100,
            resourceRecordsPerRrset=20,
            rrsetAdditionsPerChange=100,
            rrsetDeletionsPerChange=100,
            rrsetsPerManagedZone=10000,
            totalRrdataSizePerChange=10000,
        ))
    self.mocked_dns_client.projects.Get.Expect(
        self.messages_beta.DnsProjectsGetRequest(project=test_project.id),
        test_project)

    result = self.Run('dns project-info describe {0}'.format(test_project.id))
    self.assertEqual(test_project, result)

    self.AssertOutputContains("""\
id: fake-project
kind: dns#project
number: '1234567'
quota:
  kind: dns#quota
  managedZones: 100
  resourceRecordsPerRrset: 20
  rrsetAdditionsPerChange: 100
  rrsetDeletionsPerChange: 100
  rrsetsPerManagedZone: 10000
  totalRrdataSizePerChange: 10000
""", normalize_space=True)


if __name__ == '__main__':
  test_case.main()
