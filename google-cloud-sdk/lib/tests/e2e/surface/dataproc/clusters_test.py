# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import e2e_base


class ClustersIntegrationTest(e2e_base.DataprocIntegrationTestBase):
  """Integration test for all cluster commands.

  See DataprocIntegrationTestBase for requirements of tests that create
  clusters.
  """

  def testAllClustersCommands(self):
    """Run all tests as one test case reuse a cluster when sharded."""
    self.CreateClusterWithRetries()

    self.DoTestClusterUpdate()

    self.DoTestClusterDiagnose()

    self.DoTestGetSetIAMPolicy()

    self.DeleteCluster()

  def DoTestClusterUpdate(self):
    result = self.RunDataproc(
        ('clusters update {0} --num-workers 3').format(self.cluster_name))
    self.assertEqual(self.cluster_name, result.clusterName)
    self.assertEqual(
        self.messages.ClusterStatus.StateValueValuesEnum.RUNNING,
        result.status.state)
    self.assertEqual(3, result.config.workerConfig.numInstances)

  @sdk_test_base.Retry(why='clusters diagnose flakes, b/26229396')
  def DoTestClusterDiagnose(self):
    result = self.RunDataproc(
        ('clusters diagnose {0}').format(self.cluster_name))
    self.assertRegexpMatches(result, r'^gs://.*')

  def DoTestGetSetIAMPolicy(self):
    pass


class ClustersIntegrationTestGA(ClustersIntegrationTest,
                                base.DataprocTestBaseGA):
  """Integration test for all cluster commands.

  See DataprocIntegrationTestBase for requirements of tests that create
  clusters.
  """

  def testGA(self):
    self.assertEqual(self.messages,
                     core_apis.GetMessagesModule('dataproc', 'v1'))
    self.assertEqual(self.track, calliope_base.ReleaseTrack.GA)

  def DoTestGetSetIAMPolicy(self):
    self.GetSetIAMPolicy('clusters', self.cluster_name)

  def testClustersList(self):
    self.RunDataproc('clusters list --page-size=10 --limit=20')


class ClustersIntegrationTestBeta(ClustersIntegrationTest,
                                  base.DataprocTestBaseBeta):
  """Integration test for all cluster commands.

  See DataprocIntegrationTestBase for requirements of tests that create
  clusters.
  """

  def testBeta(self):
    self.assertEqual(self.messages,
                     core_apis.GetMessagesModule('dataproc', 'v1beta2'))
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)

  def DoTestGetSetIAMPolicy(self):
    self.GetSetIAMPolicy('clusters', self.cluster_name)

  def testClustersList(self):
    self.RunDataproc('clusters list --page-size=10 --limit=20')


if __name__ == '__main__':
  sdk_test_base.main()
