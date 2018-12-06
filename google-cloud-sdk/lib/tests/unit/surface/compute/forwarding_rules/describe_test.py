# -*- coding: utf-8 -*- #
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
"""Tests for the forwarding-rules describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


def SetUp(test_obj, api_version):
  test_obj.SelectApi(api_version)

  if api_version == 'v1':
    test_obj._forwarding_rules = test_resources.FORWARDING_RULES_V1
    test_obj._global_forwarding_rules = (
        test_resources.GLOBAL_FORWARDING_RULES_V1)
  elif api_version == 'beta':
    test_obj._forwarding_rules = test_resources.FORWARDING_RULES_BETA
    test_obj._global_forwarding_rules = (
        test_resources.GLOBAL_FORWARDING_RULES_BETA)
    test_obj.track = calliope_base.ReleaseTrack.BETA
  elif api_version == 'alpha':
    test_obj._forwarding_rules = test_resources.FORWARDING_RULES_ALPHA
    test_obj._global_forwarding_rules = (
        test_resources.GLOBAL_FORWARDING_RULES_ALPHA)
    test_obj.track = calliope_base.ReleaseTrack.ALPHA
  else:
    raise ValueError('Bad API version: [{0}]'.format(api_version))


class ForwardingRulesDescribeTest(test_base.BaseTest,
                                  test_case.WithOutputCapture):

  def SetUp(self):
    SetUp(self, 'v1')

  def testRegionPrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='region-1'),
            self.messages.Region(name='region-2'),
            self.messages.Region(name='region-3'),
        ],

        [self._forwarding_rules[0]],
    ])
    self.WriteInput('2\n')

    self.Run("""
        compute forwarding-rules describe forwarding-rule-1
        """)

    self.AssertErrContains('forwarding-rule-1')
    self.AssertErrContains('region-1')
    self.AssertErrContains('region-2')
    self.AssertErrContains('region-3')
    self.CheckRequests(
        self.regions_list_request,

        [(self.compute.forwardingRules,
          'Get',
          self.messages.ComputeForwardingRulesGetRequest(
              forwardingRule='forwarding-rule-1',
              region='region-1',
              project='my-project'))])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            IPAddress: 162.222.178.83
            IPProtocol: TCP
            name: forwarding-rule-1
            portRange: 1-65535
            region: https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1
            selfLink: https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/forwardingRules/forwarding-rule-1
            target: https://www.googleapis.com/compute/{api}/projects/my-project/zones/zone-1/targetInstances/target-1
            """.format(api=self.api)))

  def testWithGlobalFlag(self):
    self.make_requests.side_effect = iter([
        [self._global_forwarding_rules[0]],
    ])

    self.Run("""
        compute forwarding-rules describe global-forwarding-rule-1 --global
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules,
          'Get',
          self.messages.ComputeGlobalForwardingRulesGetRequest(
              forwardingRule='global-forwarding-rule-1',
              project='my-project'))])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            IPAddress: 162.222.178.85
            IPProtocol: TCP
            name: global-forwarding-rule-1
            portRange: 1-65535
            selfLink: https://www.googleapis.com/compute/{api}/projects/my-project/global/forwardingRules/global-forwarding-rule-1
            target: https://www.googleapis.com/compute/{api}/projects/my-project/global/targetHttpProxies/proxy-1
            """.format(api=self.api)))

  def testWithRegionFlag(self):
    self.make_requests.side_effect = iter([
        [self._forwarding_rules[0]],
    ])

    self.Run("""
        compute forwarding-rules describe forwarding-rule-1 --region region-1
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules,
          'Get',
          self.messages.ComputeForwardingRulesGetRequest(
              forwardingRule='forwarding-rule-1',
              region='region-1',
              project='my-project'))])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            IPAddress: 162.222.178.83
            IPProtocol: TCP
            name: forwarding-rule-1
            portRange: 1-65535
            region: https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1
            selfLink: https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/forwardingRules/forwarding-rule-1
            target: https://www.googleapis.com/compute/{api}/projects/my-project/zones/zone-1/targetInstances/target-1
            """.format(api=self.api)))

  def testUriSupportForRegionalForwardingRules(self):
    self.make_requests.side_effect = iter([
        [self._forwarding_rules[0]],
    ])

    self.Run("""
        compute forwarding-rules describe
          https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/forwardingRules/forwarding-rule-1
        """.format(api=self.api))

    self.CheckRequests(
        [(self.compute.forwardingRules,
          'Get',
          self.messages.ComputeForwardingRulesGetRequest(
              forwardingRule='forwarding-rule-1',
              region='region-1',
              project='my-project'))])

  def testUriSupportForGlobalForwardingRules(self):
    self.make_requests.side_effect = iter([
        [self._global_forwarding_rules[0]],
    ])

    self.Run("""
        compute forwarding-rules describe
          {uri}/projects/my-project/global/forwardingRules/global-forwarding-rule-1
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.globalForwardingRules,
          'Get',
          self.messages.ComputeGlobalForwardingRulesGetRequest(
              forwardingRule='global-forwarding-rule-1',
              project='my-project'))])

  def testUriSupportWithIllegalType(self):
    with self.AssertRaisesExceptionRegexp(
        resources.WrongResourceCollectionException, r'.*compute\.networks.*'):
      self.Run("""
          compute forwarding-rules describe
            {uri}/projects/my-project/global/networks/network-1
          """.format(uri=self.compute_uri))


class ForwardingRulesDescribeBetaTest(ForwardingRulesDescribeTest):

  def SetUp(self):
    SetUp(self, 'beta')

  def _MakeForwardingRuleWithFlexPort(self):
    prefix = 'https://www.googleapis.com/compute/'+self.api
    return self.messages.ForwardingRule(
        name='forwarding-rule-flex-port',
        IPAddress='162.222.178.84',
        IPProtocol=self.messages.ForwardingRule.IPProtocolValueValuesEnum.TCP,
        allPorts=True,
        loadBalancingScheme=self.messages.ForwardingRule.
        LoadBalancingSchemeValueValuesEnum.INTERNAL,
        region=(prefix + '/projects/my-project/regions/region-1'),
        selfLink=(prefix + '/projects/my-project/regions/'
                  'region-1/forwardingRules/forwarding-rule-flex-port'),
        backendService=(prefix + '/projects/my-project/'
                        'regions/region-1/backendServices/bs-1'))

  def testWithFlexPort(self):
    self.make_requests.side_effect = iter([
        [self._MakeForwardingRuleWithFlexPort()],
    ])

    self.Run("""
        compute forwarding-rules describe forwarding-rule-flex-port
          --region region-1
        """)

    self.CheckRequests([(self.compute.forwardingRules, 'Get',
                         self.messages.ComputeForwardingRulesGetRequest(
                             forwardingRule='forwarding-rule-flex-port',
                             region='region-1',
                             project='my-project'))])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            IPAddress: 162.222.178.84
            IPProtocol: TCP
            allPorts: true
            backendService: https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/backendServices/bs-1
            loadBalancingScheme: INTERNAL
            name: forwarding-rule-flex-port
            region: https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1
            selfLink: https://www.googleapis.com/compute/{api}/projects/my-project/regions/region-1/forwardingRules/forwarding-rule-flex-port
            """.format(api=self.api)))


if __name__ == '__main__':
  test_case.main()
