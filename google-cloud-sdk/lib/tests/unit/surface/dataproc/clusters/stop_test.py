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

"""Test of the 'clusters stop' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import unit_base


class ClusterStopUnitTestBeta(unit_base.DataprocUnitTestBase,
                              base.DataprocTestBaseBeta):
  """Tests for dataproc clusters stop."""

  def ExpectStopCluster(self,
                        cluster_name=None,
                        response=None,
                        exception=None,
                        region=None,
                        use_default_region=True):
    if not cluster_name:
      cluster_name = self.CLUSTER_NAME
    if region is None and use_default_region:
      region = self.REGION
    if not (response or exception):
      response = self.MakeOperation()
    self.mock_client.projects_regions_clusters.Stop.Expect(
        self.messages.DataprocProjectsRegionsClustersStopRequest(
            clusterName=cluster_name,
            region=region,
            projectId=self.Project(),
            requestId=self.REQUEST_ID),
        response=response,
        exception=exception)

  def ExpectStopCalls(self, error=None, region=None, use_default_region=True):
    # Stop cluster returns operation pending
    self.ExpectStopCluster(
        region=region, use_default_region=use_default_region)
    # Initial get operation returns pending
    self.ExpectGetOperation()
    # Second get operation returns done
    self.ExpectGetOperation(operation=self.MakeCompletedOperation(error=error))

  def testStopCluster(self):
    self.ExpectStopCalls()
    expected = self.MakeCompletedOperation()
    self.WriteInput('y\n')
    result = self.RunDataproc('clusters stop ' + self.CLUSTER_NAME)
    self.AssertErrContains(
        "Cluster 'test-cluster' is stopping.")
    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertMessagesEqual(expected, result)

  def testStopClusterDecline(self):
    self.WriteInput('n\n')
    with self.AssertRaisesExceptionMatches(
        console_io.OperationCancelledError,
        'Stopping cluster aborted by user.'):
      self.RunDataproc('clusters stop ' + self.CLUSTER_NAME)
      self.AssertErrContains(
          "Cluster 'test-cluster' is stopping.")
      self.AssertErrContains('PROMPT_CONTINUE')

  def testStopClusterOperationFailure(self):
    self.ExpectStopCalls(error=self.MakeRpcError())
    with self.AssertRaisesExceptionMatches(
        exceptions.OperationError,
        'Operation [{0}] failed: There was an error with the operation!'.format(
            self.OperationName())):
      self.RunDataproc('clusters stop ' + self.CLUSTER_NAME)

  def testStopClusterNotFound(self):
    self.ExpectStopCluster(
        self.CLUSTER_NAME, exception=self.MakeHttpError(404))
    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: Resource not found.'):
      self.RunDataproc('clusters stop ' + self.CLUSTER_NAME)

  def testStopClustersAsync(self):
    expected = self.MakeOperation()
    self.ExpectStopCluster(response=expected)
    result = self.RunDataproc(
        'clusters stop {0} --async'.format(self.CLUSTER_NAME))
    self.AssertErrContains('Stopping [{0}] with operation [{1}].'.format(
        self.ClusterUri(), self.OperationName()))
    self.AssertMessagesEqual(expected, result)

  def testStopClusterNoOperationGetPermission(self):
    operation = self.MakeOperation()
    self.ExpectStopCluster(
        response=operation)
    self.WriteInput('y\n')
    self.ExpectGetOperation(
        operation=operation,
        exception=self.MakeHttpError(403))
    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc('clusters stop {0}'.format(self.CLUSTER_NAME))

  def testStopClusterWithRegionProperty(self):
    properties.VALUES.dataproc.region.Set('us-central1')
    self.ExpectStopCalls(region='us-central1')
    expected = self.MakeCompletedOperation()
    self.WriteInput('y\n')
    result = self.RunDataproc('clusters stop {}'.format(self.CLUSTER_NAME))
    self.AssertErrContains("Cluster 'test-cluster' is stopping.")
    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertMessagesEqual(expected, result)

  def testStopClusterWithoutRegion(self):
    # No region is specified via flag or config.
    regex = r'Failed to find attribute \[region\]'
    with self.assertRaisesRegex(handlers.ParseError, regex):
      self.RunDataproc('clusters stop ' + self.CLUSTER_NAME, set_region=False)


if __name__ == '__main__':
  sdk_test_base.main()
