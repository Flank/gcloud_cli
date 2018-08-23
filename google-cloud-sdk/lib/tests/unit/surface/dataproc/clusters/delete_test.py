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

"""Test of the 'clusters delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.console import console_io
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import unit_base


class ClustersDeleteUnitTest(unit_base.DataprocUnitTestBase):
  """Tests for dataproc clusters delete."""

  def ExpectDeleteCluster(
      self, cluster_name=None, response=None, exception=None):
    if not cluster_name:
      cluster_name = self.CLUSTER_NAME
    if not (response or exception):
      response = self.MakeOperation()
    self.mock_client.projects_regions_clusters.Delete.Expect(
        self.messages.DataprocProjectsRegionsClustersDeleteRequest(
            clusterName=cluster_name,
            region=self.REGION,
            projectId=self.Project(),
            requestId=self.REQUEST_ID),
        response=response,
        exception=exception)

  def ExpectDeleteCalls(self, error=None):
    # Create cluster returns operation pending
    self.ExpectDeleteCluster()
    # Initial get operation returns pending
    self.ExpectGetOperation()
    # Second get operation returns done
    self.ExpectGetOperation(operation=self.MakeCompletedOperation(error=error))

  def testDeleteCluster(self):
    self.ExpectDeleteCalls()
    expected = self.MakeCompletedOperation()
    self.WriteInput('y\n')
    result = self.RunDataproc('clusters delete ' + self.CLUSTER_NAME)
    self.AssertErrContains(
        "The cluster 'test-cluster' and all attached disks will be deleted.")
    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertMessagesEqual(expected, result)

  def testDeleteClusterDecline(self):
    self.WriteInput('n\n')
    with self.AssertRaisesExceptionMatches(
        console_io.OperationCancelledError,
        'Deletion aborted by user.'):
      self.RunDataproc('clusters delete ' + self.CLUSTER_NAME)
      self.AssertErrContains(
          "The cluster 'test-cluster' and all attached disks will be deleted.")
      self.AssertErrContains('PROMPT_CONTINUE')

  def testDeleteClusterOperationFailure(self):
    self.ExpectDeleteCalls(error=self.MakeRpcError())
    with self.AssertRaisesExceptionMatches(
        exceptions.OperationError,
        'Operation [{0}] failed: There was an error with the operation!'.format(
            self.OperationName())):
      self.RunDataproc('clusters delete ' + self.CLUSTER_NAME)

  def testDeleteClusterNotFound(self):
    self.ExpectDeleteCluster(
        self.CLUSTER_NAME, exception=self.MakeHttpError(404))
    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: Resource not found.'):
      self.RunDataproc('clusters delete ' + self.CLUSTER_NAME)

  def testDeleteClustersAsync(self):
    expected = self.MakeOperation()
    self.ExpectDeleteCluster(response=expected)
    result = self.RunDataproc(
        'clusters delete {0} --async'.format(self.CLUSTER_NAME))
    self.AssertErrContains('Deleting [{0}] with operation [{1}].'.format(
        self.ClusterUri(), self.OperationName()))
    self.AssertMessagesEqual(expected, result)

  def testDeleteHiddenFlags(self):
    """Tests flags that cover flags hidden in all tracks."""
    self.ExpectDeleteCalls()
    expected = self.MakeCompletedOperation()
    self.WriteInput('y\n')
    result = self.RunDataproc((
        'clusters delete {cluster} '
        '--timeout {timeout} '
        '--quiet '
    ).format(
        cluster=self.CLUSTER_NAME,
        timeout='42s'))
    self.AssertMessagesEqual(expected, result)

  def testDeleteClusterNoOperationGetPermission(self):
    operation = self.MakeOperation()
    self.ExpectDeleteCluster(
        response=operation)
    self.WriteInput('y\n')
    self.ExpectGetOperation(
        operation=operation,
        exception=self.MakeHttpError(403))
    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc('clusters delete {0}'.format(self.CLUSTER_NAME))


class ClustersDeleteUnitTestBeta(ClustersDeleteUnitTest,
                                 base.DataprocTestBaseBeta):
  """Tests for dataproc clusters delete."""

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)


if __name__ == '__main__':
  sdk_test_base.main()
