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
"""Unit tests for the backend_services flags module."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.compute.backend_services import flags
from tests.lib import test_case

alpha_messages = core_apis.GetMessagesModule('compute', 'alpha')
beta_messages = core_apis.GetMessagesModule('compute', 'beta')


class FlagsTest(test_case.TestCase):

  def SetUp(self):
    self.choices = None
    self.parser = parser_extensions.ArgumentParser(
        calliope_command='flags-test',
    )
    self.StartObjectPatch(self.parser,
                          'add_argument',
                          side_effect=self.MockAddArgument)

  def MockAddArgument(self, *args, **kwargs):
    self.choices = sorted(kwargs.get('choices').keys())

  def testSessionAffinityChoices_InternalLb(self):
    expected_choices = sorted(
        beta_messages.BackendService.SessionAffinityValueValuesEnum.names())
    flags.AddSessionAffinity(self.parser, internal_lb=True)
    self.assertEqual(expected_choices, self.choices)

  def testSessionAffinityChoices_Beta(self):
    expected_choices = sorted(set(
        beta_messages.BackendService.SessionAffinityValueValuesEnum.names()) -
                              set(['CLIENT_IP_PROTO', 'CLIENT_IP_PORT_PROTO']))
    flags.AddSessionAffinity(self.parser, internal_lb=False)
    self.assertEqual(expected_choices, self.choices)


if __name__ == '__main__':
  test_case.main()
