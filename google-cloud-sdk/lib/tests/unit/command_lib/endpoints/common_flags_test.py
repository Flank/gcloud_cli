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

"""Unit tests for service_management common_flags module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from googlecloudsdk.command_lib.endpoints import common_flags
from tests.lib import completer_test_base
from tests.lib.surface.endpoints import unit_test_base
from six.moves import range


class CompletionTest(unit_test_base.EV1UnitTestBase,
                     completer_test_base.CompleterBase):

  def SetUp(self):
    self.num_services = 10
    self.services = [self.CreateService('service-name%d' % i)
                     for i in range(self.num_services)]

  def testProducerServiceCompletion(self):
    mocked_response = self.services_messages.ListServicesResponse(
        services=self.services)
    self.mocked_client.services.List.Expect(
        request=self.services_messages.ServicemanagementServicesListRequest(
            consumerId=None,
            producerProjectId='fake-project',
            pageSize=2000,
        ),
        response=mocked_response
    )

    self.RunCompleter(
        common_flags.ProducerServiceCompleter,
        expected_command=[
            'endpoints',
            'services',
            'list',
            '--format=disable',
            '--flatten=serviceName',
            '--quiet',
        ],
        args={
        },
        expected_completions=[service.serviceName for service in self.services],
        cli=self.cli,
    )


if __name__ == '__main__':
  completer_test_base.main()
