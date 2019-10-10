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
"""Tests that exercise the 'gcloud dns policies update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util


class UpdateTest(base.DnsMockTest):

  def _ExpectUpdate(self,
                    description=None,
                    name_servers=None,
                    networks=None,
                    forwarding=None,
                    logging=None):
    get_output = util.GetPolicies(networks=[], num=1).pop()
    expected_output = util.GetPolicies(networks=[], num=1).pop()
    get_req = self.messages.DnsPoliciesGetRequest(
        project=self.Project(), policy='mypolicy0')
    self.client.policies.Get.Expect(request=get_req, response=get_output)
    if description:
      expected_output.description = 'New Description'

    if networks:
      expected_output.networks = util.GetPolicyNetworks(networks)

    if name_servers:
      expected_output.alternativeNameServerConfig = (
          util.GetAltNameServerConfig(name_servers))

    if forwarding is not None:
      expected_output.enableInboundForwarding = forwarding

    if logging is not None:
      expected_output.enableLogging = logging

    update_req = self.messages.DnsPoliciesUpdateRequest(
        policy=expected_output.name,
        policyResource=expected_output,
        project=self.Project())
    expected_response = self.messages.PoliciesUpdateResponse(
        policy=expected_output)
    self.client.policies.Update.Expect(
        request=update_req, response=expected_response)

    return expected_response

  def testUpdateDescription(self):
    expected_response = self._ExpectUpdate(description='New Description')

    actual_output = self.Run('dns policies update mypolicy0 '
                             '--description "New Description"')
    self.assertEqual(expected_response.policy, actual_output)

  def testUpdateNameServers(self):
    expected_response = self._ExpectUpdate(name_servers=['1.0.1.1', '1.0.1.2'])
    actual_output = self.Run('dns policies update mypolicy0 '
                             '--alternative-name-servers 1.0.1.1,1.0.1.2')
    self.assertEqual(expected_response.policy, actual_output)

  def testUpdateNetworks(self):
    expected_response = self._ExpectUpdate(networks=['networka', 'networkb'])
    actual_output = self.Run('dns policies update mypolicy0 '
                             '--networks networka,networkb')
    self.assertEqual(expected_response.policy, actual_output)

  def testUpdateRemoveNameServers(self):
    expected_response = self._ExpectUpdate(name_servers=[''])
    actual_output = self.Run('dns policies update mypolicy0 '
                             '--alternative-name-servers ""')
    self.assertEqual(expected_response.policy, actual_output)
    self.assertIsNone(expected_response.policy.alternativeNameServerConfig)

  def testUpdateRemoveNetworks(self):
    expected_response = self._ExpectUpdate(networks=[''])
    actual_output = self.Run('dns policies update mypolicy0 ' '--networks ""')
    self.assertEqual(expected_response.policy, actual_output)
    self.assertFalse(expected_response.policy.networks)

  def testUpdateForwarding(self):
    expected_response = self._ExpectUpdate(forwarding=True)
    actual_output = self.Run('dns policies update mypolicy0 '
                             '--enable-inbound-forwarding')
    self.assertEqual(expected_response.policy, actual_output)

  def testUpdateLogging(self):
    expected_response = self._ExpectUpdate(logging=True)
    actual_output = self.Run('dns policies update mypolicy0 '
                             '--enable-logging')
    self.assertEqual(expected_response.policy, actual_output)

  def testUpdateAll(self):
    expected_response = self._ExpectUpdate(
        name_servers=['1.0.1.1', '1.0.1.2'],
        networks=['networka', 'networkb'],
        description='New Description',
        forwarding=True,
        logging=True)
    actual_output = self.Run('dns policies update mypolicy0 '
                             '--description "New Description" '
                             '--alternative-name-servers 1.0.1.1,1.0.1.2 '
                             '--networks networka,networkb '
                             '--enable-inbound-forwarding '
                             '--enable-logging ')
    self.assertEqual(expected_response.policy, actual_output)

  def testUpdateNone(self):
    expected_output = util.GetPolicies(networks=[], num=1).pop()
    get_req = self.messages.DnsPoliciesGetRequest(
        project=self.Project(), policy='mypolicy0')
    self.client.policies.Get.Expect(request=get_req, response=expected_output)
    actual_output = self.Run('dns policies update mypolicy0')
    self.assertEqual(expected_output, actual_output)
    self.AssertErrContains('Nothing to update.')


if __name__ == '__main__':
  test_case.main()
