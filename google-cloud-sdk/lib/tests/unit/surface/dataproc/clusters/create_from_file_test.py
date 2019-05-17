# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Test of the 'clusters create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os

from googlecloudsdk import calliope
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import compute_base
from tests.lib.surface.dataproc import unit_base


class ClustersCreateFromFileUnitTest(unit_base.DataprocUnitTestBase,
                                     compute_base.BaseComputeUnitTest):
  """Tests for dataproc clusters create-from-file."""

  def ExpectCreateCluster(
      self, cluster=None, response=None, region=None, exception=None):
    if not region:
      region = self.REGION
    if not cluster:
      cluster = self.MakeCluster()
    if not (response or exception):
      response = self.MakeOperation()
    self.mock_client.projects_regions_clusters.Create.Expect(
        self.messages.DataprocProjectsRegionsClustersCreateRequest(
            cluster=cluster,
            region=region,
            projectId=cluster.projectId,
            requestId=self.REQUEST_ID),
        response=response,
        exception=exception)

  def ExpectCreateCalls(self,
                        request_cluster=None,
                        response_cluster=None,
                        region=None,
                        error=None):
    if not request_cluster:
      request_cluster = self.MakeCluster()
    # Create request_cluster returns operation pending
    self.ExpectCreateCluster(cluster=request_cluster, region=region)
    # Initial get operation returns pending
    self.ExpectGetOperation()
    # Second get operation returns done
    self.ExpectGetOperation(operation=self.MakeCompletedOperation(error=error))
    if not error:
      # Get the request_cluster to display it.
      self.ExpectGetCluster(cluster=response_cluster, region=region)


class ClustersCreateFromFileUnitTestBeta(ClustersCreateFromFileUnitTest,
                                         base.DataprocTestBaseBeta):

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope.base.ReleaseTrack.BETA)

  def testCreateFromFile(self):
    expected_request_cluster = self.MakeCluster()
    expected_response_cluster = copy.deepcopy(expected_request_cluster)
    expected_response_cluster.status = self.messages.ClusterStatus(
        state=self.messages.ClusterStatus.StateValueValuesEnum.RUNNING)

    file_name = os.path.join(self.temp_path, 'cluster.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=expected_request_cluster, stream=stream)
    self.ExpectCreateCalls(
        request_cluster=expected_request_cluster,
        response_cluster=expected_response_cluster)

    result = self.RunDataproc(
        'clusters create-from-file --file {0}'.format(file_name))
    self.AssertMessagesEqual(expected_response_cluster, result)

  def testCreateFromFileAsync(self):
    expected_request_cluster = self.MakeCluster()
    expected_response_cluster = copy.deepcopy(expected_request_cluster)
    expected_response_cluster.status = self.messages.ClusterStatus(
        state=self.messages.ClusterStatus.StateValueValuesEnum.RUNNING)

    file_name = os.path.join(self.temp_path, 'cluster.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=expected_request_cluster, stream=stream)
    self.ExpectCreateCluster(cluster=expected_request_cluster)

    self.RunDataproc(
        'clusters create-from-file --file {0} --async'.format(file_name))
    self.AssertOutputEquals('')
    self.AssertErrContains('Creating [{0}] with operation [{1}].'.format(
        self.ClusterUri(), self.OperationName()))

  def testCreateFromFileWithRegionProperty(self):
    properties.VALUES.dataproc.region.Set('us-test1')

    expected_request_cluster = self.MakeCluster()
    expected_response_cluster = copy.deepcopy(expected_request_cluster)
    expected_response_cluster.status = self.messages.ClusterStatus(
        state=self.messages.ClusterStatus.StateValueValuesEnum.RUNNING)

    file_name = os.path.join(self.temp_path, 'cluster.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=expected_request_cluster, stream=stream)
    self.ExpectCreateCalls(
        request_cluster=expected_request_cluster,
        response_cluster=expected_response_cluster,
        region='us-test1')

    result = self.RunDataproc(
        'clusters create-from-file --file {0}'.format(file_name))
    self.AssertMessagesEqual(expected_response_cluster, result)


class ClustersCreateFromFileUnitTestAlpha(ClustersCreateFromFileUnitTestBeta,
                                          base.DataprocTestBaseAlpha):
  pass


if __name__ == '__main__':
  sdk_test_base.main()
