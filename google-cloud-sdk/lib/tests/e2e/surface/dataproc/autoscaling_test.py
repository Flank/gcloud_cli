# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Integration test for the 'dataproc clusters' commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.command_lib.export import util as export_util
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import e2e_base


class AutoscalingIntegrationTestBeta(e2e_base.DataprocIntegrationTestBase,
                                     base.DataprocTestBaseBeta):
  """Tests for managing autoscaling-policies and managing autoscaling clusters.

  See DataprocIntegrationTestBase for requirements of tests that create
  clusters.
  """

  def MakeImportableAutoscalingPolicy(self):
    return self.messages.AutoscalingPolicy(
        basicAlgorithm=self.messages.BasicAutoscalingAlgorithm(
            cooldownPeriod='120s',
            yarnConfig=self.messages.BasicYarnAutoscalingConfig(
                scaleUpFactor=1.0,
                scaleDownFactor=1.0,
                gracefulDecommissionTimeout='3600s')),
        workerConfig=self.messages.InstanceGroupAutoscalingPolicyConfig(
            maxInstances=100, minInstances=2),
        secondaryWorkerConfig=self.messages
        .InstanceGroupAutoscalingPolicyConfig(maxInstances=0, minInstances=0))

  # Ephemeral autoscaling-policy scoped to a with-statement.
  @contextlib.contextmanager
  def CreatedPolicy(self, policy_id):
    policy = self.MakeImportableAutoscalingPolicy()
    self.WriteInput(export_util.Export(message=policy))

    try:
      yield self.RunDataproc('autoscaling-policies import {0}'.format(
          policy_id))
    finally:
      self.RunDataproc('autoscaling-policies delete {0} --quiet'.format(
          policy_id))

  def testPoliciesImport_create(self):
    with self.CreatedPolicy(self.autoscaling_policy_id) as created:
      # tests that import yields the version returned from the server
      self.assertEqual(self.autoscaling_policy_id, created.id)
      self.assertEqual(self.autoscaling_policy_id, created.name.split('/')[-1])

  def testPoliciesDescribe(self):
    with self.CreatedPolicy(self.autoscaling_policy_id) as created:
      described_policy = self.RunDataproc(
          'autoscaling-policies describe {0}'.format(
              self.autoscaling_policy_id))
      # Unlike export, describe yields all the fields of a policy. Its output
      # should match the response from a successful create policy request.
      self.assertEqual(created, described_policy)

  def testPoliciesList(self):
    with self.CreatedPolicy(self.autoscaling_policy_id) as created:
      listed_policies = list(self.RunDataproc('autoscaling-policies list'))

      # We can't assert about the contents of the list, because there could be
      # other policies in the project. Instead, just make sure our created
      # policy is in the list
      listed_ids = [p.id for p in listed_policies]
      self.assertIn(created.id, listed_ids)

  def testPoliciesImport_update(self):
    with self.CreatedPolicy(self.autoscaling_policy_id):
      new_request = self.MakeImportableAutoscalingPolicy()
      new_request.basicAlgorithm.cooldownPeriod = '3600s'
      self.WriteInput(export_util.Export(message=new_request))
      updated = self.RunDataproc(
          'autoscaling-policies import --quiet {0}'.format(
              self.autoscaling_policy_id))
      self.assertEqual(self.autoscaling_policy_id, updated.id)
      self.assertEqual('3600s', updated.basicAlgorithm.cooldownPeriod)

  def testPoliciesDelete(self):
    # The with block creates and then deletes a policy
    with self.CreatedPolicy(self.autoscaling_policy_id):
      pass

    # This tests that the delete call actually succeeded
    with self.AssertRaisesHttpExceptionMatches('NOT_FOUND'):
      self.RunDataproc('autoscaling-policies describe {0}'.format(
          self.autoscaling_policy_id))

  def testPoliciesGetSetIAMPolicy(self):
    with self.CreatedPolicy(self.autoscaling_policy_id):
      self.GetSetIAMPolicy('autoscaling-policies', self.autoscaling_policy_id)

  # All cluster tests should be combined into this one test because clusters
  # are expensive to create. Note: the test doesn't explicitly delete the
  # cluster. That is done in DataprocIntegrationTestBase.tearDown.
  def testCreateAndUpdateAutoscalingCluster(self):
    with self.CreatedPolicy(self.autoscaling_policy_id):
      with self.CreatedPolicy(self.another_autoscaling_policy_id):
        try:
          created = self.CreateCluster('--autoscaling-policy {0}'.format(
              self.autoscaling_policy_id))
          created_policy_uri = created.config.autoscalingConfig.policyUri
          self.assertEqual(self.autoscaling_policy_id,
                           created_policy_uri.split('/')[-1])

          updated = self.RunDataproc(
              'clusters update {0} --autoscaling-policy {1}'.format(
                  self.cluster_name, self.another_autoscaling_policy_id))
          updated_policy_uri = updated.config.autoscalingConfig.policyUri
          self.assertEqual(self.another_autoscaling_policy_id,
                           updated_policy_uri.split('/')[-1])
        finally:
          # Need to delete the cluster before we can delete the policies
          self.DeleteCluster()


if __name__ == '__main__':
  sdk_test_base.main()
