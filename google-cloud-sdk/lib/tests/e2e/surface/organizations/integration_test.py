# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.organizations import testbase


class OrganizationIntegrationTest(testbase.OrganizationsE2ETestBase):

  def SetUp(self):
    super(OrganizationIntegrationTest, self).SetUp()
    properties.VALUES.core.user_output_enabled.Set(False)

  def compareOrganizations(self, expected, other):
    return expected.name == other.name and expected.owner == other.owner

  def testDescribeOrganization(self):
    org_id = self.TEST_ORGANIZATION.name[len('organizations/'):]

    result = self.RunOrganizations('describe', org_id)

    self.assertTrue(
        self.compareOrganizations(self.TEST_ORGANIZATION, result))

  def testListOrganizations(self):
    result = self.RunOrganizations('list')
    # Result is a generator. Get everything into a list so we can iterate over
    # multiple times.
    orgs = list(result)
    expected = self.TEST_ORGANIZATION
    matching_orgs = [o for o in orgs if self.compareOrganizations(expected, o)]
    self.assertEqual(1, len(matching_orgs),
                     'Expected organizations list result to contain '
                     'test organization: \n{0}\n\n'
                     'Actual result is: \n{1}'.format(expected, orgs))

  def testGetIamPolicy(self):
    policy = self.RunOrganizations(
        'get-iam-policy',
        self.TEST_ORGANIZATION.name[len('organizations/'):])
    self.assertIsInstance(policy, self.messages.Policy)


if __name__ == '__main__':
  test_case.main()
