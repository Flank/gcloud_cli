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
"""Tests for organizations list."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.surface.organizations import testbase


class OrganizationsListTest(testbase.OrganizationsUnitTestBase):

  messages = testbase.OrganizationsUnitTestBase.messages

  TEST_ORG_1 = messages.Organization(
      name='organizations/298357488294',
      displayName='Test Organization For Testing',
      owner=messages.OrganizationOwner(directoryCustomerId='C0123n456'))
  TEST_ORG_2 = messages.Organization(
      name='organizations/309468599305',
      displayName='A Secondary Organization',
      owner=messages.OrganizationOwner(directoryCustomerId='C9876n543'))

  def testNoFlagsEmptyList(self):
    self.mock_client.organizations.Search.Expect(
        self.messages.SearchOrganizationsRequest(),
        self.messages.SearchOrganizationsResponse())
    self.RunOrganizations('list')
    self.AssertOutputEquals('', normalize_space=True)

  def testListOneOrganization(self):
    self.mock_client.organizations.Search.Expect(
        self.messages.SearchOrganizationsRequest(),
        self.messages.SearchOrganizationsResponse(
            organizations=[self.TEST_ORG_1]))
    self.RunOrganizations('list')
    self.AssertOutputContains("""\
      DISPLAY_NAME                   ID  DIRECTORY_CUSTOMER_ID
      Test Organization For Testing  298357488294     C0123n456
      """,
                              normalize_space=True)

  def testListMultipleOrganizationsSortedById(self):
    self.mock_client.organizations.Search.Expect(
        self.messages.SearchOrganizationsRequest(),
        self.messages.SearchOrganizationsResponse(
            organizations=[self.TEST_ORG_2, self.TEST_ORG_1]))
    self.RunOrganizations('list')
    self.AssertOutputContains("""\
      DISPLAY_NAME                   ID  DIRECTORY_CUSTOMER_ID
      Test Organization For Testing  298357488294     C0123n456
      A Secondary Organization       309468599305     C9876n543
      """,
                              normalize_space=True)

  def testFilter(self):
    filter_string = 'owner.directoryCustomerId=C9876n543'
    # Filter string does NOT get passed through to the server since query lang
    # is different for gcloud vs. OnePlatform.
    self.mock_client.organizations.Search.Expect(
        self.messages.SearchOrganizationsRequest(),
        self.messages.SearchOrganizationsResponse(
            organizations=[self.TEST_ORG_1, self.TEST_ORG_2]))
    self.RunOrganizations('list', '--filter={0}'.format(filter_string))
    self.AssertOutputContains("""\
      DISPLAY_NAME                   ID  DIRECTORY_CUSTOMER_ID
      A Secondary Organization       309468599305     C9876n543
      """,
                              normalize_space=True)

  def testPagination(self):
    test_token = 'next1'
    # First page
    self.mock_client.organizations.Search.Expect(
        self.messages.SearchOrganizationsRequest(pageSize=1),
        self.messages.SearchOrganizationsResponse(
            organizations=[self.TEST_ORG_1], nextPageToken=test_token))
    # Second page
    self.mock_client.organizations.Search.Expect(
        self.messages.SearchOrganizationsRequest(
            pageSize=1, pageToken=test_token),
        self.messages.SearchOrganizationsResponse(
            organizations=[self.TEST_ORG_2]))
    self.RunOrganizations('list', '--page-size=1')
    self.AssertOutputContains("""\
      DISPLAY_NAME                   ID  DIRECTORY_CUSTOMER_ID
      Test Organization For Testing  298357488294     C0123n456
      DISPLAY_NAME                   ID  DIRECTORY_CUSTOMER_ID
      A Secondary Organization       309468599305     C9876n543
      """,
                              normalize_space=True)

  def testLimit(self):
    self.mock_client.organizations.Search.Expect(
        self.messages.SearchOrganizationsRequest(),
        self.messages.SearchOrganizationsResponse(
            organizations=[self.TEST_ORG_1, self.TEST_ORG_2]))
    self.RunOrganizations('list', '--limit=1')
    self.AssertOutputContains("""\
      DISPLAY_NAME                   ID  DIRECTORY_CUSTOMER_ID
      Test Organization For Testing  298357488294     C0123n456
      """,
                              normalize_space=True)


if __name__ == '__main__':
  test_case.main()
