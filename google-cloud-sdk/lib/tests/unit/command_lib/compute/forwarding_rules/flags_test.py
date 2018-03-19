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
"""Unit tests for the forwarding_rules flags module."""

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.compute.forwarding_rules import flags
from tests.lib import test_case

beta_messages = core_apis.GetMessagesModule('compute', 'beta')
v1_messages = core_apis.GetMessagesModule('compute', 'v1')


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
    self.choices = sorted(kwargs.get('choices'))

  def testIPProtocolsGA(self):
    expected_choices = sorted(
        v1_messages.ForwardingRule.IPProtocolValueValuesEnum.names())
    flags.AddIPProtocols(self.parser)
    self.assertEqual(expected_choices, self.choices)


if __name__ == '__main__':
  test_case.main()
