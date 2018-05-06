# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Integration tests for creating/deleting firewalls."""

from __future__ import absolute_import
from __future__ import unicode_literals
import logging

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class FirewallsTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.firewall_names_used = []
    self.GetFirewallName()

  def GetFirewallName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up
    self.firewall_name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix='gcloud-compute-test-firewall'))
    self.egress_firewall_name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix='gcloud-compute-firewall-egress-deny'))
    self.firewall_names_used.append(self.firewall_name)
    self.firewall_names_used.append(self.egress_firewall_name)

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    for name in self.firewall_names_used:
      self.CleanUpResource(name, 'firewall-rules',
                           scope=e2e_test_base.GLOBAL)

  def testFirewalls(self):
    self._TestCreateFirewall()
    self._TestUpdateFirewall()
    self._TestDeleteFirewall()

  def testEgressFirewalls(self):
    self._CreateEgressFirewall()
    self._DeleteEgressFirewall()

  def _TestCreateFirewall(self):
    self.Run('compute firewall-rules create {0} --allow tcp:80,tcp:443'
             ' --source-tags unicorns'.format(self.firewall_name))
    self.Run('compute firewall-rules describe {0}'.format(self.firewall_name))
    self.AssertNewOutputContains('name: {0}'.format(self.firewall_name),
                                 reset=False)
    self.AssertNewOutputContains("ports:\n  - '80'", reset=False)
    self.AssertNewOutputContains("ports:\n  - '443'", reset=False)
    self.AssertNewOutputContains('sourceTags:\n- unicorns')

  def _TestUpdateFirewall(self):
    # Clear sourceTags and add targetTags.
    self.Run('compute firewall-rules update {0} --target-tags target1'
             ' --source-tags \'\''.format(self.firewall_name))
    self.Run('compute firewall-rules describe {0}'.format(self.firewall_name))
    self.AssertNewOutputContains('targetTags:\n- target1', reset=False)
    self.AssertNewOutputContains("ports:\n  - '80'", reset=False)
    self.AssertNewOutputContains("ports:\n  - '443'", reset=False)
    self.AssertNewOutputNotContains('sourceTags:')

  def _TestDeleteFirewall(self):
    self.Run('compute firewall-rules list')
    self.AssertNewOutputContains(self.firewall_name)
    self.WriteInput('y\n')
    self.Run('compute firewall-rules delete {0}'.format(self.firewall_name))
    self.ClearInput()
    self.AssertNewErrContains(
        'The following firewalls will be deleted', reset=False)
    self.AssertNewErrContains(self.firewall_name)
    self.Run('compute firewall-rules list')
    self.AssertNewOutputNotContains(self.firewall_name)

  def _CreateEgressFirewall(self):
    # Create one egress deny firewall.
    self.Run('compute firewall-rules create {0} --action deny '
             '--rules tcp:9000,udp:1000-2000,icmp '
             '--direction out --destination-ranges 10.128.1.0/24 '
             '--priority 900'.format(self.firewall_name))
    self.Run('compute firewall-rules describe {0}'.format(
        self.firewall_name))
    self.AssertNewOutputContains('name: {0}'.format(self.firewall_name),
                                 reset=False)
    self.AssertNewOutputContains('denied:\n', reset=False)
    self.AssertNewOutputContains("ports:\n  - '9000'", reset=False)
    self.AssertNewOutputContains('ports:\n  - 1000-2000', reset=False)
    self.AssertNewOutputContains('- IPProtocol: icmp', reset=False)
    self.AssertNewOutputContains('destinationRanges:\n- 10.128.1.0/24',
                                 reset=False)
    self.AssertNewOutputContains('direction: EGRESS', reset=False)
    self.AssertNewOutputContains('priority: 900')

  def _DeleteEgressFirewall(self):
    self.Run('compute firewall-rules list')
    self.AssertNewOutputContains(self.firewall_name)
    self.WriteInput('y\n')
    self.Run('compute firewall-rules delete {0}'.format(
        self.firewall_name))
    self.ClearInput()
    self.AssertNewErrContains(
        'The following firewalls will be deleted', reset=False)
    self.AssertNewErrContains(self.firewall_name)
    self.Run('compute firewall-rules list')
    self.AssertNewOutputNotContains(self.firewall_name)


class BetaFirewallsTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.firewall_names_used = []
    self.GetFirewallName()

  def GetFirewallName(self):
    self.firewall_name_disabled = next(
        e2e_utils.GetResourceNameGenerator(prefix='firewall-disabled'))
    self.firewall_name_enabled = next(
        e2e_utils.GetResourceNameGenerator(prefix='firewall-enabled'))
    self.firewall_names_used.append(self.firewall_name_disabled)
    self.firewall_names_used.append(self.firewall_name_enabled)

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    for name in self.firewall_names_used:
      self.CleanUpResource(name, 'firewall-rules', scope=e2e_test_base.GLOBAL)

  def testDisabledFirewalls(self):
    self._TestCreateDisabledFirewall()
    self._TestCreateEnabledFirewall()
    self._TestUpdateFirewall_disabledToEnabled()
    self._TestUpdateFirewall_enabledToDisabled()

  def _TestCreateDisabledFirewall(self):
    self.Run('compute firewall-rules create {0} --allow tcp:80,tcp:443'
             ' --disabled'.format(self.firewall_name_disabled))
    self.Run('compute firewall-rules describe {0}'.format(
        self.firewall_name_disabled))
    self.AssertNewOutputContains(
        'name: {0}'.format(self.firewall_name_disabled), reset=False)
    self.AssertNewOutputContains("ports:\n  - '80'", reset=False)
    self.AssertNewOutputContains("ports:\n  - '443'", reset=False)
    self.AssertNewOutputContains('disabled: true')

  def _TestCreateEnabledFirewall(self):
    self.Run('compute firewall-rules create {0} --allow tcp:80,tcp:443'
             ' --no-disabled'.format(self.firewall_name_enabled))
    self.Run('compute firewall-rules describe {0}'.format(
        self.firewall_name_enabled))
    self.AssertNewOutputContains(
        'name: {0}'.format(self.firewall_name_enabled), reset=False)
    self.AssertNewOutputContains("ports:\n  - '80'", reset=False)
    self.AssertNewOutputContains("ports:\n  - '443'", reset=False)
    self.AssertNewOutputContains('disabled: false')

  def _TestUpdateFirewall_disabledToEnabled(self):
    self.Run('compute firewall-rules update {0} --target-tags target1'
             ' --no-disabled'.format(self.firewall_name_disabled))
    self.Run('compute firewall-rules describe {0}'.format(
        self.firewall_name_disabled))
    self.AssertNewOutputContains("ports:\n  - '80'", reset=False)
    self.AssertNewOutputContains("ports:\n  - '443'", reset=False)
    self.AssertNewOutputNotContains('disabled: true')

  def _TestUpdateFirewall_enabledToDisabled(self):
    self.Run('compute firewall-rules update {0} --target-tags target1'
             ' --disabled'.format(self.firewall_name_enabled))
    self.Run('compute firewall-rules describe {0}'.format(
        self.firewall_name_enabled))
    self.AssertNewOutputContains("ports:\n  - '80'", reset=False)
    self.AssertNewOutputContains("ports:\n  - '443'", reset=False)
    self.AssertNewOutputNotContains('disabled: false')


class AlphaFirewallsTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.firewall_names_used = []
    self.GetFirewallName()

  def GetFirewallName(self):
    self.firewall_name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix='gcloud-compute-test-firewall'))
    self.firewall_names_used.append(self.firewall_name)

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    for name in self.firewall_names_used:
      self.CleanUpResource(name, 'firewall-rules', scope=e2e_test_base.GLOBAL)

  def testFirewallLogging(self):
    self._TestCreateLoggingFirewall()

  def _TestCreateLoggingFirewall(self):
    # Create one egress deny firewall.
    self.Run('compute firewall-rules create {0} --action deny '
             '--rules tcp:9000,udp:1000-2000,icmp '
             '--direction out --destination-ranges 10.128.1.0/24 '
             '--priority 900 --enable-logging'.format(self.firewall_name))
    self.Run('compute firewall-rules describe {0}'.format(self.firewall_name))
    self.AssertNewOutputContains(
        'name: {0}'.format(self.firewall_name), reset=False)
    self.AssertNewOutputContains('denied:\n', reset=False)
    self.AssertNewOutputContains("ports:\n  - '9000'", reset=False)
    self.AssertNewOutputContains('ports:\n  - 1000-2000', reset=False)
    self.AssertNewOutputContains('- IPProtocol: icmp', reset=False)
    self.AssertNewOutputContains(
        'destinationRanges:\n- 10.128.1.0/24', reset=False)
    self.AssertNewOutputContains('direction: EGRESS', reset=False)
    self.AssertNewOutputContains('priority: 900', reset=False)
    self.AssertNewOutputContains('enableLogging: true')


if __name__ == '__main__':
  e2e_test_base.main()
