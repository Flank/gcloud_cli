# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Unit tests for endpoints services get-iam-policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.endpoints import services_util

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.endpoints import unit_test_base

GET_REQUEST = (services_util.GetMessagesModule()
               .ServicemanagementServicesGetIamPolicyRequest)


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class EndpointsGetIamPolicyTest(unit_test_base.EV1UnitTestBase):
  """Unit tests for endpoints services get-iam-policy command."""

  def testGetIamPolicy(self, track):
    self.track = track
    bindings = [
        self.services_messages.Binding(
            role='roles/servicemanagement.serviceConsumer',
            members=['user:test1@google.com', 'user:test2@google.com']),
    ]
    mocked_response = self.services_messages.Policy(bindings=bindings)

    self.mocked_client.services.GetIamPolicy.Expect(
        request=GET_REQUEST(
            servicesId=self.DEFAULT_SERVICE_NAME),
        response=mocked_response
    )

    response = self.Run(
        'endpoints services get-iam-policy %s' % self.DEFAULT_SERVICE_NAME)
    self.assertEqual(response, mocked_response)

  def testListCommandFilter(self, track):
    self.track = track
    bindings = [
        self.services_messages.Binding(
            role='roles/servicemanagement.serviceConsumer',
            members=['user:test1@google.com', 'user:test2@google.com']),
    ]
    mocked_response = self.services_messages.Policy(bindings=bindings)

    self.mocked_client.services.GetIamPolicy.Expect(
        request=GET_REQUEST(
            servicesId=self.DEFAULT_SERVICE_NAME),
        response=mocked_response
    )

    self.Run("""
        endpoints services get-iam-policy {}
        --flatten=bindings[].members
        --filter=bindings.role:roles/servicemanagement.serviceConsumer
        --format=table[no-heading](bindings.members:sort=1)
        """.format(self.DEFAULT_SERVICE_NAME))
    self.AssertOutputEquals('user:test1@google.com\nuser:test2@google.com\n')


if __name__ == '__main__':
  test_case.main()
