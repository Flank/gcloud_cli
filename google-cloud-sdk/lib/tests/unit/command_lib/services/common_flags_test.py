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

"""Unit tests for services common_flags module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.services import common_flags
from tests.lib import completer_test_base
from tests.lib.surface.services import unit_test_base
from six.moves import range  # pylint: disable=redefined-builtin


class CompletionTest(unit_test_base.SUUnitTestBase,
                     completer_test_base.CompleterBase):

  def SetUp(self):
    self.project = 'fake-project'
    self.num_services = 10
    self.services = [
        'service-name{0}'.format(i) for i in range(self.num_services)
    ]
    self.service_configs = [
        self._NewServiceConfig(self.project, s) for s in self.services
    ]

  def testConsumerServiceCompletion(self):
    mocked_response = self.services_messages.ListServicesResponse(
        services=self.service_configs)

    self.mocked_client.services.List.Expect(
        request=self.services_messages.ServiceusageServicesListRequest(
            parent='projects/{0}'.format(self.project), filter='state:ENABLED'),
        response=mocked_response)

    self.RunCompleter(
        common_flags.ConsumerServiceCompleter,
        expected_command=[
            'beta',
            'services',
            'list',
            '--format=disable',
            '--flatten=config.name',
            '--quiet',
            '--enabled',
        ],
        args={
            '--enabled': True,
        },
        expected_completions=self.services,
        cli=self.cli,
    )


if __name__ == '__main__':
  completer_test_base.main()
