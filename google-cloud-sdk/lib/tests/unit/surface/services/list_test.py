# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Unit tests for services list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties

from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.services import unit_test_base

import httplib2
from six.moves import range  # pylint: disable=redefined-builtin


class ServicesListTest(unit_test_base.SV1UnitTestBase):
  """Unit tests for services list command."""

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

    self.num_services = 10
    self.services = [self.CreateService('service-name%d.googleapis.com' % i)
                     for i in range(self.num_services)]

  def testServicesListEnabled(self):
    mocked_response = self.services_messages.ListServicesResponse(
        services=self.services)

    self.mocked_client.services.List.Expect(
        request=self.services_messages.ServicemanagementServicesListRequest(
            consumerId='project:fake-project'
        ),
        response=mocked_response
    )

    response = self.Run('services list --enabled')
    self.assertEqual(response, self.services)

  def testServicesListWithLimit(self):
    num_limit = 3
    mocked_response = self.services_messages.ListServicesResponse(
        services=self.services)

    self.mocked_client.services.List.Expect(
        request=self.services_messages.ServicemanagementServicesListRequest(
            consumerId='project:fake-project'
        ),
        response=mocked_response
    )

    response = self.Run('services list --enabled --limit=%s' % num_limit)
    self.assertEqual(response, self.services[:num_limit])

  def testServicesListWithLimitUnlimited(self):
    mocked_response = self.services_messages.ListServicesResponse(
        services=self.services)

    self.mocked_client.services.List.Expect(
        request=self.services_messages.ServicemanagementServicesListRequest(
            consumerId='project:fake-project'
        ),
        response=mocked_response
    )

    response = self.Run('services list --enabled --limit=unlimited')
    self.assertEqual(response, self.services)

  def testServicesListEnabledDefault(self):
    mocked_response = self.services_messages.ListServicesResponse(
        services=self.services)

    self.mocked_client.services.List.Expect(
        request=self.services_messages.ServicemanagementServicesListRequest(
            consumerId='project:fake-project'
        ),
        response=mocked_response
    )

    response = self.Run('services list')
    self.assertEqual(response, self.services)

  def testServicesListEnabledForSpecificProject(self):
    project_id = 'my-specified-project'
    mocked_response = self.services_messages.ListServicesResponse(
        services=self.services)

    self.mocked_client.services.List.Expect(
        request=self.services_messages.ServicemanagementServicesListRequest(
            consumerId='project:' + project_id
        ),
        response=mocked_response
    )

    response = self.Run(
        'services list --enabled --project %s' % project_id)
    self.assertEqual(response, self.services)

  def testServicesListAvailable(self):
    mocked_response = self.services_messages.ListServicesResponse(
        services=self.services)

    self.mocked_client.services.List.Expect(
        request=self.services_messages.ServicemanagementServicesListRequest(),
        response=mocked_response
    )

    response = self.Run('services list --available')
    self.assertEqual(response, self.services)


class ServicesListOutputTest(unit_test_base.SV1UnitTestBase,
                             sdk_test_base.WithOutputCapture):
  """Unit tests for services list command."""

  def SetUp(self):
    self.num_services = 10
    self.services = [
        self.CreateService('service-name%d.googleapis.com' %
                           (self.num_services - i - 1))
        for i in range(self.num_services)]

  def testServicesListEnabledDefaultOutput(self):
    mocked_response = self.services_messages.ListServicesResponse(
        services=self.services)

    self.mocked_client.services.List.Expect(
        request=self.services_messages.ServicemanagementServicesListRequest(
            consumerId='project:fake-project'
        ),
        response=mocked_response
    )

    self.Run('services list')
    self.AssertOutputEquals("""\
NAME TITLE
service-name0.googleapis.com.googleapis.com
service-name1.googleapis.com.googleapis.com
service-name2.googleapis.com.googleapis.com
service-name3.googleapis.com.googleapis.com
service-name4.googleapis.com.googleapis.com
service-name5.googleapis.com.googleapis.com
service-name6.googleapis.com.googleapis.com
service-name7.googleapis.com.googleapis.com
service-name8.googleapis.com.googleapis.com
service-name9.googleapis.com.googleapis.com
""", normalize_space=True)


class ListAlphaTest(unit_test_base.SUUnitTestBase):
  """Unit tests for services list command."""
  OPERATION_NAME = 'operations/abc.0000000000'

  def testList(self):
    self.ExpectListServicesCall()

    self.Run('alpha services list --available')
    self.AssertOutputEquals(
        """\
NAME TITLE
service-name-1.googleapis.com
service-name.googleapis.com
""",
        normalize_space=True)


# DO NOT REMOVE THIS TEST.
# The services API should always use gcloud's shared quota.
class QuotaHeaderTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth,
                      parameterized.TestCase):
  """Make sure user project quota is disabled for this API."""

  def SetUp(self):
    properties.VALUES.core.project.Set('foo')
    self.request_mock = self.StartObjectPatch(
        httplib2.Http, 'request',
        return_value=(httplib2.Response({'status': 200}), b''))

  @parameterized.parameters(
      (None, 'beta', None),
      (None, '', None),
      (properties.VALUES.billing.LEGACY, 'beta', None),
      (properties.VALUES.billing.LEGACY, '', None),
      (properties.VALUES.billing.CURRENT_PROJECT, 'beta', b'foo'),
      (properties.VALUES.billing.CURRENT_PROJECT, '', b'foo'),
      ('bar', 'beta', b'bar'),
      ('bar', '', b'bar'),
  )
  def testQuotaHeader(self, prop_value, track, header_value):
    properties.VALUES.billing.quota_project.Set(prop_value)
    self.Run(track + ' services list')
    header = self.request_mock.call_args[0][3].get(b'X-Goog-User-Project', None)
    self.assertEqual(header, header_value)


if __name__ == '__main__':
  test_case.main()
