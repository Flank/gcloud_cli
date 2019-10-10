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

"""E2E tests for the 'gcloud dns' commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.util import retry
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.surface.dns import base


class PolicyTest(base.DnsTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.id_gen = e2e_utils.GetResourceNameGenerator(
        prefix='dns-cloud', delimiter='-')
    self.delete_retryer = retry.Retryer(
        max_retrials=3, exponential_sleep_multiplier=2)

  @contextlib.contextmanager
  def _CreatePolicy(self):
    policy_name = next(self.id_gen)
    created = False
    try:
      self.Run('dns policies create {} --description "Test Policy" '
               '--networks=""'.format(policy_name))
      created = True
      yield policy_name
    finally:
      if created:
        self.delete_retryer.RetryOnException(
            self.Run, [('dns policies delete {} --quiet'.format(policy_name))])

  @contextlib.contextmanager
  def _CreateTestNetwork(self, prefix):
    created = False
    name = '{}-test-network'.format(prefix)
    try:
      self.Run(
          'compute networks create {} '
          '--subnet-mode auto'.format(name),
          track=calliope_base.ReleaseTrack.GA)
      created = True
      yield name
    finally:
      if created:
        self.delete_retryer.RetryOnException(
            self.Run, [('compute networks delete {} --quiet'.format(name))],
            {'track': calliope_base.ReleaseTrack.GA})

  def testScenario(self):
    """CRUD Lifecycle Test for Cloud DNS Policies."""
    with self._CreatePolicy() as test_policy:
      self.ClearOutput()
      self.Run('dns policies list')
      self.AssertOutputContains(test_policy)
      before_policy = self.Run('dns policies describe {}'.format(test_policy))
      self.assertFalse(before_policy.enableInboundForwarding)
      self.assertFalse(before_policy.enableLogging)
      self.assertEqual('Test Policy', before_policy.description)
      self.assertFalse(before_policy.networks)
      with self._CreateTestNetwork(test_policy) as test_network:
        updated_policy = self.Run('dns policies update {} --description "{}" '
                                  '--enable-inbound-forwarding '
                                  '--enable-logging '
                                  '--networks {}'.format(
                                      test_policy, 'New Test Description',
                                      test_network))
        self.assertTrue(updated_policy.enableInboundForwarding)
        self.assertTrue(updated_policy.enableLogging)
        self.assertEqual('New Test Description', updated_policy.description)
        self.assertTrue(updated_policy.networks)
        self.assertIn(test_network, updated_policy.networks[0].networkUrl)
        self.Run('dns policies update {} --networks ""'.format(test_policy))


if __name__ == '__main__':
  test_case.main()
