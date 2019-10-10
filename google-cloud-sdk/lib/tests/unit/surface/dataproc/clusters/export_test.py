# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Test of the 'clusters export' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os
from googlecloudsdk import calliope
from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.console import console_io
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import compute_base
from tests.lib.surface.dataproc import unit_base


class ClustersExportUnitTest(unit_base.DataprocUnitTestBase,
                             compute_base.BaseComputeUnitTest):
  """Tests for clusters export."""
  pass


class ClustersExportUnitTestBeta(ClustersExportUnitTest):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.BETA

  def testExportClustersToStdOut(self):
    cluster = self.MakeCluster()

    # Expected output has cluster-specific info cleared.
    expected_output = copy.deepcopy(cluster)
    expected_output.clusterName = None
    expected_output.projectId = None

    self.ExpectGetCluster(cluster)
    self.RunDataproc('clusters export {0}'.format(self.CLUSTER_NAME))
    self.AssertOutputEquals(export_util.Export(expected_output))

  def testExportClustersHttpError(self):
    self.ExpectGetCluster(exception=self.MakeHttpError(403))
    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc('clusters export {0}'.format(self.CLUSTER_NAME))

  def testExportClustersToFile(self):
    dataproc = dp.Dataproc(calliope.base.ReleaseTrack.BETA)
    msgs = dataproc.messages
    cluster = self.MakeCluster()

    # Expected output has cluster-specific info cleared.
    expected_output = copy.deepcopy(cluster)
    expected_output.clusterName = None
    expected_output.projectId = None

    self.ExpectGetCluster(cluster)

    file_name = os.path.join(self.temp_path, 'cluster.yaml')
    result = self.RunDataproc('clusters export {0} --destination {1}'.format(
        self.CLUSTER_NAME, file_name))
    self.assertIsNone(result)
    data = console_io.ReadFromFileOrStdin(file_name or '-', binary=False)
    exported_template = export_util.Import(
        message_type=msgs.Cluster, stream=data)
    self.AssertMessagesEqual(expected_output, exported_template)


class ClustersExportUnitTestAlpha(ClustersExportUnitTestBeta):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  sdk_test_base.main()
