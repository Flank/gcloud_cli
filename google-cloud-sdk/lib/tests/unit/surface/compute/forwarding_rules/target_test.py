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
"""Tests for the forwarding-rules set-target subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class GlobalForwardingRulesSetTargetTest(test_base.BaseTest):

  def testSimpleCaseWithGlobalTargetHttpProxy(self):
    self.Run("""
        compute forwarding-rules set-target forwarding-rule-1
          --global
          --target-http-proxy target-http-proxy-1
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules,
          'SetTarget',
          self.messages.ComputeGlobalForwardingRulesSetTargetRequest(
              forwardingRule='forwarding-rule-1',
              project='my-project',
              targetReference=self.messages.TargetReference(
                  target=(
                      'https://www.googleapis.com/compute/{api}/projects/'
                      'my-project/global/targetHttpProxies/'
                      'target-http-proxy-1').format(api=self.api),
              )))],
    )

  def testSimpleCaseWithGlobalTargetHttpsProxy(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules set-target forwarding-rule-1
          --global
          --target-https-proxy target-https-proxy-1
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules,
          'SetTarget',
          messages.ComputeGlobalForwardingRulesSetTargetRequest(
              forwardingRule='forwarding-rule-1',
              project='my-project',
              targetReference=messages.TargetReference(
                  target=(
                      self.compute_uri + '/projects/'
                      'my-project/global/targetHttpsProxies/'
                      'target-https-proxy-1'),
              )))],
    )

  def testSimpleCaseWithGlobalTargetSslProxy(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules set-target forwarding-rule-1
          --global
          --target-ssl-proxy target-ssl-proxy-1
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules,
          'SetTarget',
          messages.ComputeGlobalForwardingRulesSetTargetRequest(
              forwardingRule='forwarding-rule-1',
              project='my-project',
              targetReference=messages.TargetReference(
                  target=(
                      self.compute_uri + '/projects/'
                      'my-project/global/targetSslProxies/'
                      'target-ssl-proxy-1'),
              )))],
    )

  def testSimpleCaseWithGlobalTargetTcpProxy(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules set-target forwarding-rule-1
          --global
          --target-tcp-proxy target-tcp-proxy-1
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules,
          'SetTarget',
          messages.ComputeGlobalForwardingRulesSetTargetRequest(
              forwardingRule='forwarding-rule-1',
              project='my-project',
              targetReference=messages.TargetReference(
                  target=(
                      self.compute_uri + '/projects/'
                      'my-project/global/targetTcpProxies/'
                      'target-tcp-proxy-1'),
              )))],
    )


class RegionalForwardingRulesSetTargetTest(test_base.BaseTest):

  def testSimpleCaseWithRegion(self):
    self.Run("""
        compute forwarding-rules set-target forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules,
          'SetTarget',
          self.messages.ComputeForwardingRulesSetTargetRequest(
              forwardingRule='forwarding-rule-1',
              project='my-project',
              region='us-central2',
              targetReference=self.messages.TargetReference(
                  target=(
                      'https://www.googleapis.com/compute/{api}/projects/'
                      'my-project/regions/us-central2/targetPools/'
                      'target-pool-1').format(api=self.api),
              )))],
    )

  def testTargetPoolInstanceOption(self):
    self.Run("""
        compute forwarding-rules set-target forwarding-rule-1
          --region us-central2
          --target-instance target-instance-1
          --target-instance-zone us-central2-a
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules,
          'SetTarget',
          self.messages.ComputeForwardingRulesSetTargetRequest(
              forwardingRule='forwarding-rule-1',
              project='my-project',
              region='us-central2',
              targetReference=self.messages.TargetReference(
                  target=(
                      'https://www.googleapis.com/compute/{api}/projects/'
                      'my-project/zones/us-central2-a/targetInstances/'
                      'target-instance-1').format(api=self.api),
              )))],
    )

  def testRegionalAndZonalPrompting(self):
    # TODO(b/36049934): Investigate mocking at a lower level in order to
    # test zone filtering

    # TODO(b/36057402): Prompt for zone only and use
    # utils.ZoneNameToRegionName() to derive region?

    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.WriteInput('3\n')
    self.WriteInput('1\n')
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='us-central1'),
            self.messages.Region(name='us-central2'),
        ],
        [
            self.messages.Zone(name='us-central2-a'),
            self.messages.Zone(name='us-central2-b'),
        ],

        [],
    ])
    self.Run("""
        compute forwarding-rules set-target forwarding-rule-1
          --target-instance target-instance-1
        """)

    self.CheckRequests(
        self.regions_list_request,

        [(self.compute.zones,
          'List',
          self.messages.ComputeZonesListRequest(
              filter='name eq us-central2.*',
              maxResults=500,
              project='my-project'))],

        [(self.compute.forwardingRules,
          'SetTarget',
          self.messages.ComputeForwardingRulesSetTargetRequest(
              forwardingRule='forwarding-rule-1',
              project='my-project',
              region='us-central2',
              targetReference=self.messages.TargetReference(
                  target=(
                      'https://www.googleapis.com/compute/{api}/projects/'
                      'my-project/zones/us-central2-a/targetInstances/'
                      'target-instance-1').format(api=self.api),
              )))],
    )
    self.AssertErrContains('forwarding rule:')
    self.AssertErrContains('forwarding-rule-1')
    self.AssertErrContains('us-central1')
    self.AssertErrContains('us-central2')
    self.AssertErrContains('target instance:')
    self.AssertErrContains('target-instance-1')
    self.AssertErrContains('zone:')
    self.AssertErrContains('us-central2-a')
    self.AssertErrContains('us-central2-b')


class ForwardingRulesSetTargetTestAlpha(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testBackendService(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules set-target forwarding-rule-1
          --region alaska
          --backend-service crab-fishing
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules,
          'SetTarget',
          messages.ComputeForwardingRulesSetTargetRequest(
              forwardingRule='forwarding-rule-1',
              project='my-project',
              region='alaska',
              targetReference=messages.TargetReference(
                  target=(
                      self.compute_uri + '/projects/'
                      'my-project/regions/alaska/backendServices/'
                      'crab-fishing'),
              )))],
    )

  def testTargetHttpProxy(self):
    self.Run("""
        compute forwarding-rules set-target forwarding-rule-1
          --region us-central1
          --target-http-proxy target-http-proxy-1
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'SetTarget',
          self.messages.ComputeForwardingRulesSetTargetRequest(
              forwardingRule='forwarding-rule-1',
              project='my-project',
              region='us-central1',
              targetReference=self.messages.TargetReference(
                  target=('https://www.googleapis.com/compute/{api}/projects/'
                          'my-project/global/targetHttpProxies/'
                          'target-http-proxy-1').format(api=self.api),)))],)
    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testTargetHttpsProxy(self):
    self.Run("""
        compute forwarding-rules set-target forwarding-rule-1
          --region us-central1
          --target-https-proxy target-https-proxy-1
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'SetTarget',
          self.messages.ComputeForwardingRulesSetTargetRequest(
              forwardingRule='forwarding-rule-1',
              project='my-project',
              region='us-central1',
              targetReference=self.messages.TargetReference(
                  target=('https://www.googleapis.com/compute/{api}/projects/'
                          'my-project/global/targetHttpsProxies/'
                          'target-https-proxy-1').format(api=self.api),)))],)
    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testTargetSslProxy(self):
    self.Run("""
        compute forwarding-rules set-target forwarding-rule-1
          --region us-central1
          --target-ssl-proxy target-ssl-proxy-1
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'SetTarget',
          self.messages.ComputeForwardingRulesSetTargetRequest(
              forwardingRule='forwarding-rule-1',
              project='my-project',
              region='us-central1',
              targetReference=self.messages.TargetReference(
                  target=('https://www.googleapis.com/compute/{api}/projects/'
                          'my-project/global/targetSslProxies/'
                          'target-ssl-proxy-1').format(api=self.api),)))],)
    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testTargetTcpProxy(self):
    self.Run("""
        compute forwarding-rules set-target forwarding-rule-1
          --region us-central1
          --target-tcp-proxy target-tcp-proxy-1
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'SetTarget',
          self.messages.ComputeForwardingRulesSetTargetRequest(
              forwardingRule='forwarding-rule-1',
              project='my-project',
              region='us-central1',
              targetReference=self.messages.TargetReference(
                  target=('https://www.googleapis.com/compute/{api}/projects/'
                          'my-project/global/targetTcpProxies/'
                          'target-tcp-proxy-1').format(api=self.api),)))],)
    self.AssertOutputEquals('')
    self.AssertErrEquals('')


if __name__ == '__main__':
  test_case.main()
