# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for the forwarding-rules delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute import flags as compute_flags
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class GlobalForwardingRulesDeleteTest(test_base.BaseTest):

  def testMissingRuleErrorPrintsTwoFlags(self):
    with self.assertRaisesRegex(
        compute_flags.UnderSpecifiedResourceError,
        r'Underspecified resource \[forwarding-rule-9]. Specify one of the '
        r'\[--global, --region] flags.'):
      self.Run('compute forwarding-rules delete forwarding-rule-9')

  def testRegionGlobalFlagsMutuallyExclusive(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --global: At most one of --global | --region '
        'may be specified'):
      self.Run("""
          compute forwarding-rules delete forwarding-rule-1
            --region us-central1
            --global
          """)

    self.CheckRequests()

  def testSimpleCaseWithGlobal(self):
    self.Run("""
        compute forwarding-rules delete forwarding-rule-1
          --global
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules,
          'Delete',
          self.messages.ComputeGlobalForwardingRulesDeleteRequest(
              forwardingRule='forwarding-rule-1',
              project='my-project',
          ))],
    )

  def testUriSupport(self):
    self.WriteInput('y\n')
    self.Run("""
        compute forwarding-rules delete forwarding-rule-1
          {uri}/projects/my-project/global/forwardingRules/forwarding-rule-2
          --global
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.globalForwardingRules,
          'Delete',
          self.messages.ComputeGlobalForwardingRulesDeleteRequest(
              forwardingRule='forwarding-rule-1',
              project='my-project',
          )),

         (self.compute.globalForwardingRules,
          'Delete',
          self.messages.ComputeGlobalForwardingRulesDeleteRequest(
              forwardingRule='forwarding-rule-2',
              project='my-project',
          ))],
    )

    self.AssertErrContains(
        r'The following global forwarding rules will be deleted:\n'
        r' - [forwarding-rule-1]\n'
        r' - [forwarding-rule-2]')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testGlobalPrompting(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.WriteInput('1\n')
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='us-central1'),
            self.messages.Region(name='us-central2'),
        ],

        [],
    ])
    self.Run("""
        compute forwarding-rules delete forwarding-rule-1
        """)

    self.CheckRequests(
        self.regions_list_request,

        [(self.compute.globalForwardingRules,
          'Delete',
          self.messages.ComputeGlobalForwardingRulesDeleteRequest(
              forwardingRule='forwarding-rule-1',
              project='my-project',
          ))],
    )
    self.AssertErrContains('forwarding-rule-1')
    self.AssertErrContains('global')
    self.AssertErrContains('us-central1')
    self.AssertErrContains('us-central2')


class RegionalForwardingRulesDeleteTest(test_base.BaseTest):

  def testSimpleCaseWithRegion(self):
    self.Run("""
        compute forwarding-rules delete forwarding-rule-1
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules,
          'Delete',
          self.messages.ComputeForwardingRulesDeleteRequest(
              forwardingRule='forwarding-rule-1',
              project='my-project',
              region='us-central2',
          ))],
    )
    self.AssertErrContains(
        r'The following forwarding rules will be deleted:\n'
        r' - [forwarding-rule-1] in [us-central2]')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testUriSupport(self):
    self.Run("""
        compute forwarding-rules delete forwarding-rule-1
             {uri}/projects/my-project/regions/us-central2/forwardingRules/forwarding-rule-2
          --region us-central2
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.forwardingRules,
          'Delete',
          self.messages.ComputeForwardingRulesDeleteRequest(
              forwardingRule='forwarding-rule-1',
              project='my-project',
              region='us-central2',
          )),
         (self.compute.forwardingRules,
          'Delete',
          self.messages.ComputeForwardingRulesDeleteRequest(
              forwardingRule='forwarding-rule-2',
              project='my-project',
              region='us-central2',
          ))],
    )

  def testRegionalPrompting(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.WriteInput('3\n')
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='us-central1'),
            self.messages.Region(name='us-central2'),
        ],

        [],
    ])
    self.Run("""
        compute forwarding-rules delete forwarding-rule-1
        """)

    self.CheckRequests(
        self.regions_list_request,

        [(self.compute.forwardingRules,
          'Delete',
          self.messages.ComputeForwardingRulesDeleteRequest(
              forwardingRule='forwarding-rule-1',
              project='my-project',
              region='us-central2',
          ))],
    )
    self.AssertErrContains('forwarding-rule-1')
    self.AssertErrContains('us-central1')
    self.AssertErrContains('us-central2')


if __name__ == '__main__':
  test_case.main()
