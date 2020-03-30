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

"""Test of the 'clusters diagnose' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import extra_types

from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.api_lib.dataproc import storage_helpers
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import unit_base
import mock


class ClustersDiagnoseUnitTest(unit_base.DataprocUnitTestBase):
  """Tests for dataproc clusters diagnose."""

  def SetUp(self):
    self.mock_stream = mock.create_autospec(
        storage_helpers.StorageObjectSeriesStream)

    def fake_read_into_writable(stream):
      stream.write('Some diagnose output.\n')
    self.mock_stream.ReadIntoWritable.side_effect = fake_read_into_writable
    self.StartObjectPatch(
        storage_helpers,
        'StorageObjectSeriesStream',
        return_value=self.mock_stream)

    # By default always report the stream is open.
    self.mock_stream_open = mock.PropertyMock(return_value=True)
    type(self.mock_stream).open = self.mock_stream_open

  def ExpectDiagnoseCluster(self, response=None, exception=None, region=None):
    if not (response or exception):
      response = self.MakeOperation()
    if region is None:
      region = self.REGION

    self.mock_client.projects_regions_clusters.Diagnose.Expect(
        self.messages.DataprocProjectsRegionsClustersDiagnoseRequest(
            clusterName=self.CLUSTER_NAME,
            region=region,
            projectId=self.Project()),
        response=response,
        exception=exception)

  def ExpectDiagnoseCalls(self, response=None, region=None):
    response = self.messages.Operation.ResponseValue()
    response.additionalProperties = [
        self.messages.Operation.ResponseValue.AdditionalProperty(
            key='@type', value=extra_types.JsonValue(string_value='some-type')),
        self.messages.Operation.ResponseValue.AdditionalProperty(
            key='outputUri',
            value=extra_types.JsonValue(string_value='gs://example/output')),
    ]
    self.ExpectDiagnoseCluster(region=region)
    self.ExpectGetOperation()
    self.ExpectGetOperation(
        operation=self.MakeCompletedOperation(response=response))

  def testDiagnoseCluster(self):
    self.ExpectDiagnoseCalls()
    self.mock_stream_open.side_effect = [True, True, False]
    result = self.RunDataproc('clusters diagnose ' + self.CLUSTER_NAME)
    self.assertEqual('gs://example/output', result)
    self.AssertErrNotContains('output did not finish streaming')

  def testDiagnoseClusterOutputWarning(self):
    self.ExpectDiagnoseCalls()
    result = self.RunDataproc('clusters diagnose ' + self.CLUSTER_NAME)
    self.assertEqual('gs://example/output', result)
    self.AssertErrContains('output did not finish streaming')

  def testDiagnoseClusterOperationFailure(self):
    self.ExpectDiagnoseCluster()
    self.ExpectGetOperation()
    self.ExpectGetOperation(
        operation=self.MakeCompletedOperation(error=self.MakeRpcError()))
    with self.AssertRaisesExceptionMatches(
        exceptions.OperationError,
        'Operation [{0}] failed: There was an error with the operation!'.format(
            self.OperationName())):
      self.RunDataproc('clusters diagnose ' + self.CLUSTER_NAME)

  def testDiagnoseClusterNotFound(self):
    self.ExpectDiagnoseCluster(exception=self.MakeHttpError(
        404, 'Cluster not found.'))
    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: Cluster not found.'):
      self.RunDataproc('clusters diagnose ' + self.CLUSTER_NAME)

  def testDiagnoseClusterHiddenFlags(self):
    self.ExpectDiagnoseCalls()
    result = self.RunDataproc((
        'clusters diagnose {0} '
        '--timeout 42s '
        ).format(self.CLUSTER_NAME))
    self.assertEqual('gs://example/output', result)

  def testDiagnoseClusterNoGetOperationPermission(self):
    operation = self.MakeOperation()
    self.ExpectDiagnoseCluster(response=operation)
    self.ExpectGetOperation(
        operation=operation, exception=self.MakeHttpError(403))
    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc((
          'clusters diagnose {0}'
      ).format(self.CLUSTER_NAME))

  def testDiagnoseClusterWithRegionProperty(self):
    properties.VALUES.dataproc.region.Set('us-central1')
    self.ExpectDiagnoseCalls(region='us-central1')
    self.mock_stream_open.side_effect = [True, True, False]
    result = self.RunDataproc('clusters diagnose ' + self.CLUSTER_NAME)
    self.assertEqual('gs://example/output', result)
    self.AssertErrNotContains('output did not finish streaming')

  def testDiagnoseClusterWithRegionFlag(self):
    properties.VALUES.dataproc.region.Set('us-central1')
    self.ExpectDiagnoseCalls(region='us-east1')
    self.mock_stream_open.side_effect = [True, True, False]
    result = self.RunDataproc('clusters diagnose {} --region us-east1'.format(
        self.CLUSTER_NAME))
    self.assertEqual('gs://example/output', result)
    self.AssertErrNotContains('output did not finish streaming')

  def testDiagnoseClusterWithoutRegionProperty(self):
    # No region is specified via flag or config.
    regex = r'Failed to find attribute \[region\]'
    with self.assertRaisesRegex(handlers.ParseError, regex):
      self.RunDataproc(
          'clusters diagnose ' + self.CLUSTER_NAME, set_region=False)


class ClustersDiagnoseUnitTestBeta(ClustersDiagnoseUnitTest,
                                   base.DataprocTestBaseBeta):
  """Tests for dataproc clusters diagnose."""

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)


class ClustersDiagnoseUnitTestAlpha(
    ClustersDiagnoseUnitTestBeta, base.DataprocTestBaseAlpha):
  pass


if __name__ == '__main__':
  sdk_test_base.main()
