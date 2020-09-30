# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for the forwarding-rules create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute.forwarding_rules import create_test_base


class PscGoogleApisForwardingRulesCreateTestAlpha(
    create_test_base.ForwardingRulesCreateTestBase):

  def testValidRequestAllApis(self):
    self.Run("""
        compute forwarding-rules create forwardingrule1
        --global
        --address=192.168.2.100
        --target-google-apis-bundle all-apis
        --network network1
    """)
    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwardingrule1',
                  target=('all-apis'),
                  network=('{compute_uri}/projects/my-project/global/networks/'
                           'network1'.format(compute_uri=self.compute_uri)),
                  IPAddress='192.168.2.100'),
              project='my-project'))],)

  def testValidRequestVpcSc(self):
    address_uri = ('http://www.googleapis.com/compute/alpha/projects/abcd/'
                   'global/addresses/efg')
    self.Run("""
        compute forwarding-rules create forwardingrule1
        --global
        --address={}
        --target-google-apis-bundle vpc-sc
        --network network1
    """.format(address_uri))
    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwardingrule1',
                  target='vpc-sc',
                  network=('{compute_uri}/projects/my-project/global/networks/'
                           'network1'.format(compute_uri=self.compute_uri)),
                  IPAddress=address_uri),
              project='my-project'))],)

  def testBadBundleNamesRejected(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.InvalidArgumentException,
        '.*valid values for target-google-apis-bundle are.*'):
      self.Run("""
          compute forwarding-rules create fr1
          --global
          --address=10.1.1.1
          --target-google-apis-bundle notabundle
          --network network1
      """)
    self.CheckRequests()

  def testBadLbTypesRejected(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.InvalidArgumentException,
        '.*--load-balancing-scheme flag is not allowed for PSC-GoogleApis.*'):
      self.Run("""
          compute forwarding-rules create forwardingrule1
          --global
          --address=10.1.1.1
          --load-balancing-scheme=INTERNAL_MANAGED
          --target-google-apis-bundle vpc-sc
          --network network1
      """)
    self.CheckRequests()

  def testNonAlnumFrNamesRejected(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.ToolException, '.*alphanumeric, starting with a letter.*'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
          --global
          --address=10.1.1.1
          --target-google-apis-bundle vpc-sc
          --network network1
      """)
    self.CheckRequests()

  def testInitialDigitFrNamesRejected(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.ToolException, '.*alphanumeric, starting with a letter.*'):
      self.Run("""
          compute forwarding-rules create 123forwarding
          --global
          --address=10.1.1.1
          --target-google-apis-bundle vpc-sc
          --network network1
      """)
    self.CheckRequests()

  def testOverlongFrName(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.ToolException, '.*alphanumeric, starting with a letter.*'):
      self.Run("""
          compute forwarding-rules create averylongforwardingrulename
          --global
          --address=10.1.1.1
          --target-google-apis-bundle vpc-sc
          --network network1
      """)
    self.CheckRequests()

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
