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
"""Base class for firewall_rules tests."""

from apitools.base.py.testing import mock as apitools_mock

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class FirewallRulesBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for all FirewallRules tests."""

  APPENGINE_API = 'appengine'
  APPENGINE_API_VERSION = 'v1'

  def _FormatApp(self):
    return 'apps/{0}'.format(self.Project())

  def _FormatFirewallRule(self, priority):
    uri = self._FormatApp()+'/firewall/ingressRules'
    if priority:
      uri += '/'+str(priority)
    return uri

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule(self.APPENGINE_API,
                                                self.APPENGINE_API_VERSION)
    self.mock_client = apitools_mock.Client(
        core_apis.GetClientClass(self.APPENGINE_API,
                                 self.APPENGINE_API_VERSION),
        real_client=core_apis.GetClientInstance(
            self.APPENGINE_API, self.APPENGINE_API_VERSION, no_http=True))
    self.mock_client.Mock()
    # If any API calls were made but weren't expected, this will throw an error
    self.addCleanup(self.mock_client.Unmock)

  def MakeFirewallRule(self, priority, source_range, description, action):
    action_enum_val = None
    if action:
      if action.upper() == 'ALLOW':
        action_enum_val = self.messages.FirewallRule.ActionValueValuesEnum.ALLOW
      elif action.upper() == 'DENY':
        action_enum_val = self.messages.FirewallRule.ActionValueValuesEnum.DENY

    return self.messages.FirewallRule(
        priority=int(priority),
        sourceRange=source_range,
        description=description,
        action=action_enum_val)

  def ExpectListFirewallRule(self, rules, matching_address=None):
    """Adds expected firewall-rules list request and response.

    Args:
      rules: messages.FirewallRule[], list of rules to expect.
      matching_address: str, an ip address to filter matching rules.
    """
    request = self.messages.AppengineAppsFirewallIngressRulesListRequest(
        parent=self._FormatApp(),
        matchingAddress=matching_address,
        pageSize=100)
    response = self.messages.ListIngressRulesResponse(
        ingressRules=rules, nextPageToken='')
    self.mock_client.AppsFirewallIngressRulesService.List.Expect(
        request, response=response)
