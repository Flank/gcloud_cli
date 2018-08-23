# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Tests for 'clusters delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from apitools.base.py import exceptions as api_exceptions

from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import util as c_util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.container import base
from six.moves import zip  # pylint: disable=redefined-builtin


class DeleteTestGA(base.GATestBase, base.ClustersTestBase):
  """gcloud GA track using container v1 API."""

  def SetUp(self):
    self.api_mismatch = False

  def HttpError(self):
    body = '''\
{
  "error": {
    "code": 400,
    "message": "your request is bad and you should feel bad.",
    "status": "INVALID_ARGUMENT"
  }
}'''
    return api_exceptions.HttpError(None, body, 'https://fake-url.io')

  def _TestDeleteOneCluster(self, location):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y\ny')
    kwargs = {'zone': location}
    cluster = self._RunningCluster(**kwargs)
    c_util.ClusterConfig.Persist(cluster, self.PROJECT_ID)
    c_config = c_util.ClusterConfig.Load(
        self.CLUSTER_NAME, location, self.PROJECT_ID)
    self._TestDefaultAuth(c_config)
    properties.PersistProperty(
        properties.VALUES.container.cluster, cluster.name)
    # Delete cluster returns operation pending
    self.ExpectDeleteCluster(
        self.CLUSTER_NAME,
        self._MakeOperation(operationType=self.op_delete, **kwargs),
        zone=location)
    # Initial get operation returns pending
    self.ExpectGetOperation(self._MakeOperation(operationType=self.op_delete,
                                                **kwargs))
    # Second get operation returns done
    self.ExpectGetOperation(self._MakeOperation(
        operationType=self.op_delete,
        status=self.op_done,
        **kwargs))
    self.ClearOutput()
    self.ClearErr()
    if location == self.REGION:
      self.Run(self.regional_clusters_command_base.format(location) +
               ' delete {0}'.format(self.CLUSTER_NAME))
    else:
      self.Run(self.clusters_command_base.format(location) +
               ' delete {0}'.format(self.CLUSTER_NAME))
    self.AssertErrContains('Deleted')
    self.AssertErrNotContains('kubeconfig')
    if self.api_mismatch and location == self.REGION:
      self.AssertErrContains('You invoked')

    self.assertIsNone(c_util.ClusterConfig.Load(
        self.CLUSTER_NAME, self.REGION, self.PROJECT_ID))
    self.assertFalse(os.path.exists(c_config.config_dir))
    self.assertIsNone(properties.VALUES.container.cluster.Get())

  def testDeleteOneCluster(self):
    self._TestDeleteOneCluster(self.ZONE)

  def testDeleteOneRegionalCluster(self):
    self._TestDeleteOneCluster(self.REGION)

  def testDeleteAsync(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self._MakeCluster()
    # Delete cluster returns operation pending
    self.ExpectDeleteCluster(
        self.CLUSTER_NAME,
        self._MakeOperation(operationType=self.op_delete))
    self.ClearOutput()
    self.ClearErr()
    self.Run(self.clusters_command_base.format(self.ZONE) +
             ' delete {0} --async --quiet'.format(self.CLUSTER_NAME))
    self.AssertErrNotContains('Deleted')
    self.AssertErrNotContains('kubeconfig')

  def testDeleteQuiet(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self._MakeCluster()
    # Delete cluster returns operation pending
    self.ExpectDeleteCluster(
        self.CLUSTER_NAME,
        self._MakeOperation(operationType=self.op_delete))
    # Initial get operation returns pending
    self.ExpectGetOperation(self._MakeOperation(operationType=self.op_delete))
    # Second get operation returns done
    self.ExpectGetOperation(self._MakeOperation(
        operationType=self.op_delete,
        status=self.op_done))
    self.ClearOutput()
    self.ClearErr()
    self.Run(self.clusters_command_base.format(self.ZONE) +
             ' delete {0} --quiet'.format(self.CLUSTER_NAME))
    self.AssertErrContains('Deleted')
    self.AssertErrNotContains('kubeconfig')

  def testDeleteAborted(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('n')
    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' delete {0}'.format(self.CLUSTER_NAME))
    self.AssertErrContains('Aborted by user.')

  def testDeleteMultipleClusters(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')
    clusters = [
        self._MakeCluster(
            name='cluster1', endpoint='1.1.1.1', currentMasterVersion='1.8.0'),
        self._MakeCluster(
            name='cluster2', endpoint='2.2.2.2', currentMasterVersion='1.8.0'),
        self._MakeCluster(
            name='cluster3', endpoint='3.3.3.3', currentMasterVersion='1.8.0'),
    ]
    for cluster in clusters:
      c_util.ClusterConfig.Persist(cluster, self.PROJECT_ID)
      self.ExpectDeleteCluster(
          cluster.name,
          self._MakeOperation(
              name=cluster.name + '-mock-operation-id',
              operationType=self.op_delete))
    for cluster in clusters:
      # return pending, done for each operation
      self.ExpectGetOperation(self._MakeOperation(
          name=cluster.name + '-mock-operation-id',
          operationType=self.op_delete))
      self.ExpectGetOperation(self._MakeOperation(
          name=cluster.name + '-mock-operation-id',
          operationType=self.op_delete,
          status=self.op_done))
    self.ClearOutput()
    self.ClearErr()
    self.Run(self.clusters_command_base.format(self.ZONE) +
             ' delete {0}'.format(' '.join(x.name for x in clusters)))
    # Operations polled only for deleteError, success clusters
    for cluster in clusters[1:]:
      self.AssertErrContains('Deleting cluster {0}'.format(cluster.name))
      self.assertIsNone(c_util.ClusterConfig.Load(
          cluster.name, self.ZONE, self.PROJECT_ID))

  def testDeleteErrors(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')

    not_found = self._MakeCluster(name='notFound', endpoint='1.1.1.1')
    wrong_zone = self._MakeCluster(name='wrongZone', endpoint='1.2.3.4')
    actual_zone = self._MakeCluster(
        name='wrongZone', zone='other-zone', endpoint='1.2.3.4')
    existing = [
        self._MakeCluster(
            name='deleteError',
            endpoint='2.2.2.2',
            currentMasterVersion='1.8.0'),
        self._MakeCluster(
            name='success', endpoint='3.3.3.3', currentMasterVersion='1.8.0'),
    ]
    clusters = [not_found, wrong_zone] + existing

    for cluster in not_found, wrong_zone:
      # return 404
      self.ExpectDeleteCluster(cluster.name, exception=base.NOT_FOUND_ERROR)
      self.ExpectListClusters(existing + [actual_zone])
    for cluster in existing:
      c_util.ClusterConfig.Persist(cluster, self.PROJECT_ID)
      mock_operation_id = cluster.name + '-mock-operation-id'
      self.ExpectDeleteCluster(
          cluster.name,
          response=self._MakeOperation(
              name=mock_operation_id,
              operationType=self.op_delete))
    for cluster, error_msg in zip(existing, ('delete failed', None)):
      # return pending, error for [deleteError], pending, success for [success]
      mock_operation_id = cluster.name + '-mock-operation-id'
      self.ExpectGetOperation(self._MakeOperation(
          name=mock_operation_id,
          operationType=self.op_delete))
      self.ExpectGetOperation(self._MakeOperation(
          name=mock_operation_id,
          operationType=self.op_delete,
          status=self.op_done,
          errorMessage=error_msg))

    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(c_util.Error):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' delete {0}'.format(' '.join(x.name for x in clusters)))
    for cluster in existing:
      self.AssertErrContains('Deleting cluster {0}'.format(cluster.name))
      self.assertIsNone(c_util.ClusterConfig.Load(
          cluster.name, self.ZONE, self.PROJECT_ID))
    self.AssertErrContains('Some requests did not succeed:')
    for line in api_adapter.WRONG_ZONE_ERROR_MSG.format(
        error=exceptions.HttpException(base.NOT_FOUND_ERROR,
                                       c_util.HTTP_ERROR_FORMAT),
        name=wrong_zone.name,
        wrong_zone=self.ZONE,
        zone='other-zone').splitlines():
      self.AssertErrContains(line)
    for line in api_adapter.NO_SUCH_CLUSTER_ERROR_MSG.format(
        error=exceptions.HttpException(base.NOT_FOUND_ERROR,
                                       c_util.HTTP_ERROR_FORMAT),
        name=not_found.name, project=self.PROJECT_ID).splitlines():
      self.AssertErrContains(line)
    self.AssertErrContains('delete failed')

  def testDeleteHttpError(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')

    cluster = self._MakeCluster(
        name='http_error', endpoint='1.2.3.4')
    self.ExpectDeleteCluster(cluster.name, exception=self.HttpError())
    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(c_util.Error):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' delete {0}'.format(cluster.name))
    self.assertIsNone(c_util.ClusterConfig.Load(
        cluster.name, self.ZONE, self.PROJECT_ID))
    self.AssertErrContains(
        'ResponseError: code=400, message=your request is bad '
        'and you should feel bad.')

  def testDeleteNoCachedConfig(self):
    # The cluster being deleted has no cached config, but add
    # second config dir to verify we don't wipe the whole folder.
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')
    other_cluster = self._MakeCluster(
        name='some-other-cluster',
        status=self.running,
        statusMessage='Running',
        endpoint=self.ENDPOINT,
        zone=self.ZONE,
        currentMasterVersion='1.8.0')
    c_util.ClusterConfig.Persist(other_cluster, self.PROJECT_ID)
    properties.PersistProperty(
        properties.VALUES.container.cluster, other_cluster.name)
    self.assertIsNone(c_util.ClusterConfig.Load(
        self.CLUSTER_NAME, self.ZONE, self.PROJECT_ID))
    # Delete cluster returns operation pending
    self._MakeCluster()
    self.ExpectDeleteCluster(
        self.CLUSTER_NAME,
        self._MakeOperation(operationType=self.op_delete))
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(
        operationType=self.op_delete,
        status=self.op_done))
    self.ClearOutput()
    self.ClearErr()
    self.Run(self.clusters_command_base.format(self.ZONE) +
             ' delete {0}'.format(self.CLUSTER_NAME))
    self.AssertErrContains('Deleted')
    self.AssertErrNotContains('kubeconfig')
    self.assertIsNone(c_util.ClusterConfig.Load(
        self.CLUSTER_NAME, self.ZONE, self.PROJECT_ID))
    c_config = c_util.ClusterConfig.Load(
        other_cluster.name, other_cluster.zone, self.PROJECT_ID)
    self.assertIsNotNone(c_config)
    self.assertEqual(properties.VALUES.container.cluster.Get(),
                     other_cluster.name)

  def testDeleteMissingEnv(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')

    # HOME is set to a tmp directory in UnitTestBase.
    # Temporarily unset HOME so we can verify expected warning.
    self.assertEqual(self.tmp_home.path, os.environ['HOME'])
    self.StartDictPatch('os.environ', {
        'HOME': '',
        'HOMEDRIVE': '',
        'HOMEPATH': '',
        'USERPROFILE': ''
    })
    self._MakeCluster()
    self.ExpectDeleteCluster(
        self.CLUSTER_NAME, self._MakeOperation(operationType=self.op_delete))
    self.ExpectGetOperation(
        self._MakeOperation(operationType=self.op_delete, status=self.op_done))
    self.ClearOutput()
    self.ClearErr()
    self.Run(self.clusters_command_base.format(self.ZONE) +
             ' delete {0}'.format(self.CLUSTER_NAME))
    self.AssertErrContains('Deleted')
    self.AssertErrContains('KUBECONFIG must be set')


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class DeleteTestBeta(base.BetaTestBase, DeleteTestGA):
  """gcloud Beta track using container v1beta1 API."""


# Mixin class must come in first to have the correct multi-inheritance behavior.
class DeleteTestAlpha(base.AlphaTestBase, DeleteTestBeta):
  """gcloud Alpha track using container v1alpha1 API."""


if __name__ == '__main__':
  test_case.main()
