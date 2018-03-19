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

"""Unit tests for services common_flags module."""

from googlecloudsdk.command_lib.services import common_flags
from tests.lib import completer_test_base
from tests.lib.surface.services import unit_test_base


class CompletionTest(unit_test_base.SV1UnitTestBase,
                     completer_test_base.CompleterBase):

  def SetUp(self):
    self.num_services = 10
    self.services = [self.CreateService('service-name%d' % i)
                     for i in range(self.num_services)]

  def testConsumerServiceCompletion(self):
    mocked_response = self.services_messages.ListServicesResponse(
        services=self.services)

    self.mocked_client.services.List.Expect(
        request=self.services_messages.ServicemanagementServicesListRequest(
            consumerId='project:fake-project'
        ),
        response=mocked_response
    )

    self.RunCompleter(
        common_flags.ConsumerServiceCompleter,
        expected_command=[
            'beta',
            'services',
            'list',
            '--format=disable',
            '--flatten=serviceName',
            '--quiet',
            '--enabled',
        ],
        args={
            '--enabled': True,
        },
        expected_completions=[service.serviceName for service in self.services],
        cli=self.cli,
    )


if __name__ == '__main__':
  completer_test_base.main()
