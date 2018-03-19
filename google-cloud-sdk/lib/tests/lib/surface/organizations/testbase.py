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
"""Base class for all organizations tests."""

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib.apitools import http_error


class OrganizationsUnitTestBase(cli_test_base.CliTestBase,
                                sdk_test_base.WithFakeAuth):
  """Base class for all Organizations unit tests with fake auth and mocks."""

  messages = apis.GetMessagesModule('cloudresourcemanager', 'v1')

  URL_ROOT = 'http://cloudresourcemanager.googleapis.com/v1/organizations/'
  GOOD_ID_URL = URL_ROOT + '12345?someParam=true&other=false'
  BAD_ID_URL = URL_ROOT + 'BAD_ID?someParam=true&other=false'
  SECRET_ID_URL = URL_ROOT + 'SECRET_ID?someParam=true&other=false'

  HTTP_403_ERR = http_error.MakeHttpError(403, url=SECRET_ID_URL)
  HTTP_404_ERR = http_error.MakeHttpError(404, url=BAD_ID_URL)
  HTTP_500_ERR = http_error.MakeHttpError(500, 'Uh oh', url=GOOD_ID_URL)

  TEST_ORGANIZATION = messages.Organization(
      name=u'organizations/298357488294',
      displayName=u'Test Organization For Testing',
      owner=messages.OrganizationOwner(directoryCustomerId=u'C0123n456'))

  def _GetTestIamPolicy(self, clear_fields=None):
    """Creates a test IAM policy.

    Args:
        clear_fields: list of policy fields to clear.
    Returns:
        IAM policy.
    """
    if clear_fields is None:
      clear_fields = []

    policy = self.messages.Policy(
        auditConfigs=[
            self.messages.AuditConfig(
                auditLogConfigs=[
                    self.messages.AuditLogConfig(
                        logType=self.messages.AuditLogConfig
                        .LogTypeValueValuesEnum.ADMIN_READ)
                ],
                service=u'allServices')
        ],
        bindings=[
            self.messages.Binding(
                role=u'roles/resourcemanager.projectCreator',
                members=[u'domain:foo.com']),
            self.messages.Binding(
                role=u'roles/resourcemanager.organizationAdmin',
                members=[u'user:admin@foo.com'])
        ],
        etag='someUniqueEtag',
        version=1)

    for field in clear_fields:
      policy.reset(field)

    return policy

  def RunOrganizations(self, *command):
    return self.Run(['organizations'] + list(command))

  def SetUp(self):
    self.mock_client = mock.Client(
        apis.GetClientClass('cloudresourcemanager', 'v1'),
        real_client=apis.GetClientInstance('cloudresourcemanager',
                                           'v1',
                                           no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)


class OrganizationsE2ETestBase(e2e_base.WithServiceAuth):
  """Base class for all Organizations E2E tests, with service auth."""

  messages = apis.GetMessagesModule('cloudresourcemanager', 'v1')

  # See b/28400331 for reference.
  TEST_ORGANIZATION = messages.Organization(
      name='organizations/961309089256',
      displayName='Elysium gCloud Testing',
      owner=messages.OrganizationOwner(directoryCustomerId='C01qz4ik7'),)

  def RunOrganizations(self, *command):
    return self.Run(['organizations'] + list(command))
