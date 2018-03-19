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
"""Tests for the forwarding-rules list subcommand."""
import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.forwarding_rules import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

import mock


def SetUp(test_obj, api_version):
  test_obj.SelectApi(api_version)
  msgs = test_obj.messages
  prefix = 'https://www.googleapis.com/compute/' + api_version

  if api_version == 'v1':
    test_obj._forwarding_rules = test_resources.FORWARDING_RULES_V1
    test_obj._global_forwarding_rules = (
        test_resources.GLOBAL_FORWARDING_RULES_V1)
  elif api_version == 'beta':
    test_obj._forwarding_rules = test_resources.FORWARDING_RULES_BETA + [
        msgs.ForwardingRule(
            name='forwarding-rule-ilb',
            IPAddress='192.168.111.11',
            IPProtocol=msgs.ForwardingRule.IPProtocolValueValuesEnum.UDP,
            loadBalancingScheme=(
                msgs.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.INTERNAL),
            ports=['80'],
            region=(prefix + '/projects/my-project/'
                    'regions/region-1'),
            selfLink=(prefix + '/projects/my-project/'
                      'regions/region-1/forwardingRules/forwarding-rule-ilb'),
            backendService=(prefix + '/projects/my-project/'
                            'regions/region-1/backendServices/service-1'))
    ]
    test_obj._global_forwarding_rules = (
        test_resources.GLOBAL_FORWARDING_RULES_BETA)
  else:
    raise ValueError('Bad API version: [{0}]'.format(api_version))

  list_json_patcher = mock.patch(
      'googlecloudsdk.api_lib.compute.request_helper.ListJson', autospec=True)
  test_obj.addCleanup(list_json_patcher.stop)
  test_obj.list_json = list_json_patcher.start()


class ForwardingRulesListTest(test_base.BaseTest,
                              completer_test_base.CompleterBase):

  def SetUp(self):
    SetUp(self, 'v1')

  def testTableOutput(self):
    command = 'compute forwarding-rules list'
    return_value = (self._forwarding_rules
                    + self._global_forwarding_rules)
    output = ("""\
        NAME                     REGION   IP_ADDRESS     IP_PROTOCOL TARGET
        forwarding-rule-1        region-1 162.222.178.83 TCP         zone-1/targetInstances/target-1
        forwarding-rule-2        region-1 162.222.178.84 UDP         region-1/targetPools/target-2
        global-forwarding-rule-1          162.222.178.85 TCP         proxy-1
        global-forwarding-rule-2          162.222.178.86 UDP         proxy-2
        """)
    self.RequestAggregate(command, return_value, output)

  def testGlobalOption(self):
    command = 'compute forwarding-rules list --uri --global'
    return_value = self._global_forwarding_rules
    output = ("""\
        https://www.googleapis.com/compute/{api}/projects/my-project/global/forwardingRules/global-forwarding-rule-1
        https://www.googleapis.com/compute/{api}/projects/my-project/global/forwardingRules/global-forwarding-rule-2
        """.format(api=self.api))

    self.RequestOnlyGlobal(command, return_value, output)

  def testRegionsWithNoArgs(self):
    command = 'compute forwarding-rules list --uri --regions ""'
    return_value = self._forwarding_rules
    output = ("""\
        https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/forwardingRules/forwarding-rule-1
        https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/forwardingRules/forwarding-rule-2
        """.format(api=self.api))

    self.RequestAggregate(command, return_value, output)

  def testOneRegion(self):
    command = 'compute forwarding-rules list --uri --regions region-1'
    return_value = self._forwarding_rules
    output = ("""\
        https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/forwardingRules/forwarding-rule-1
        https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/forwardingRules/forwarding-rule-2
        """.format(api=self.api))

    self.RequestOneRegion(command, return_value, output)

  def testMultipleRegions(self):
    command = 'compute forwarding-rules list --uri --regions region-1,region-2'
    return_value = self._forwarding_rules
    output = ("""\
        https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/forwardingRules/forwarding-rule-1
        https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/forwardingRules/forwarding-rule-2
        """.format(api=self.api))

    self.RequestTwoRegions(command, return_value, output)

  def testRegionsAndGlobal(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --global: At most one of --global | --regions '
        'may be specified.'):
      self.Run("""\
          compute forwarding-rules list --regions "" --global
          """)
    self.CheckRequests()

  def RequestOnlyGlobal(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self.compute.globalForwardingRules,
                   'List',
                   self.messages.ComputeGlobalForwardingRulesListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def RequestAggregate(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self.compute.forwardingRules,
                   'AggregatedList',
                   self.messages.ComputeForwardingRulesAggregatedListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def RequestOneRegion(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self.compute.forwardingRules,
                   'List',
                   self.messages.ComputeForwardingRulesListRequest(
                       project='my-project',
                       region='region-1'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def RequestTwoRegions(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self.compute.forwardingRules,
                   'List',
                   self.messages.ComputeForwardingRulesListRequest(
                       project='my-project',
                       region='region-1')),
                  (self.compute.forwardingRules,
                   'List',
                   self.messages.ComputeForwardingRulesListRequest(
                       project='my-project',
                       region='region-2'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def testForwardingRulesCompleter(self):
    returns = [self._forwarding_rules, self._global_forwarding_rules]
    def SideEffect(*args, **kwargs):
      del args
      del kwargs
      return iter(resource_projector.MakeSerializable(returns.pop()))
    self.list_json.side_effect = SideEffect
    self.RunCompleter(
        flags.ForwardingRulesCompleter,
        expected_command=[
            [
                'compute',
                'forwarding-rules',
                'list',
                '--global',
                '--uri',
                '--quiet',
                '--format=disable',
            ],
            [
                'compute',
                'forwarding-rules',
                'list',
                '--filter=region:*',
                '--uri',
                '--quiet',
                '--format=disable',
            ],
        ],
        expected_completions=[
            u'forwarding-rule-1',
            u'forwarding-rule-2',
            u'global-forwarding-rule-1',
            u'global-forwarding-rule-2',
        ],
        cli=self.cli,
    )


class ForwardingRulesListBetaTest(ForwardingRulesListTest):

  def SetUp(self):
    SetUp(self, 'beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testTableOutput(self):
    command = 'compute forwarding-rules list'
    return_value = (self._forwarding_rules
                    + self._global_forwarding_rules)
    output = ("""\
        NAME                     REGION   IP_ADDRESS     IP_PROTOCOL TARGET
        forwarding-rule-1        region-1 162.222.178.83 TCP         zone-1/targetInstances/target-1
        forwarding-rule-2        region-1 162.222.178.84 UDP         region-1/targetPools/target-2
        forwarding-rule-ilb      region-1 192.168.111.11 UDP         region-1/backendServices/service-1
        global-forwarding-rule-1          162.222.178.85 TCP         proxy-1
        global-forwarding-rule-2          162.222.178.86 UDP         proxy-2
        """)
    self.RequestAggregate(command, return_value, output)

  def testRegionsWithNoArgs(self):
    command = 'compute forwarding-rules list --uri --regions ""'
    return_value = self._forwarding_rules
    output = ("""\
        https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/forwardingRules/forwarding-rule-1
        https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/forwardingRules/forwarding-rule-2
        https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/forwardingRules/forwarding-rule-ilb
        """.format(api=self.api))

    self.RequestAggregate(command, return_value, output)

  def testOneRegion(self):
    command = 'compute forwarding-rules list --uri --regions region-1'
    return_value = self._forwarding_rules
    output = ("""\
        https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/forwardingRules/forwarding-rule-1
        https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/forwardingRules/forwarding-rule-2
        https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/forwardingRules/forwarding-rule-ilb
        """.format(api=self.api))

    self.RequestOneRegion(command, return_value, output)

  def testMultipleRegions(self):
    command = 'compute forwarding-rules list --uri --regions region-1,region-2'
    return_value = self._forwarding_rules
    output = ("""\
        https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/forwardingRules/forwarding-rule-1
        https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/forwardingRules/forwarding-rule-2
        https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/forwardingRules/forwarding-rule-ilb
        """.format(api=self.api))

    self.RequestTwoRegions(command, return_value, output)

  def testForwardingRulesCompleter(self):
    returns = [self._forwarding_rules, self._global_forwarding_rules]
    def SideEffect(*args, **kwargs):
      del args
      del kwargs
      return iter(resource_projector.MakeSerializable(returns.pop()))
    self.list_json.side_effect = SideEffect
    self.RunCompleter(
        flags.ForwardingRulesCompleter,
        expected_command=[
            [
                'compute',
                'forwarding-rules',
                'list',
                '--global',
                '--uri',
                '--quiet',
                '--format=disable',
            ],
            [
                'compute',
                'forwarding-rules',
                'list',
                '--filter=region:*',
                '--uri',
                '--quiet',
                '--format=disable',
            ],
        ],
        expected_completions=[
            u'forwarding-rule-1',
            u'forwarding-rule-2',
            u'forwarding-rule-ilb',
            u'global-forwarding-rule-1',
            u'global-forwarding-rule-2',
        ],
        cli=self.cli,
    )

if __name__ == '__main__':
  test_case.main()
