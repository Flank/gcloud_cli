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

"""Base for all Dataproc e2e tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as core_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import retry
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base


def ShouldRetryCreateCluster(
    exception_type, unused_exception, unused_tb, unused_state):
  """Determines if an Exception was caused by a failing Operation or timeout."""
  return issubclass(exception_type, exceptions.OperationError)


class DataprocIntegrationTestBase(
    base.DataprocTestBase, e2e_base.WithServiceAuth):
  r"""Base class for all integration Dataproc tests.

  Dataproc clusters require 3 GCE VMs (except for single node clusters) and a
  firewall with open TCP & UDP connections on all ports between them.
  They also need a Network Route mapping 0.0.0.0/0 to the
  Default internet gateway to access Dataproc and GCS APIs.

  A preconfigured network is hard coded in the tests. As of today a new
  equivalent network can be created with:
      gcloud compute networks create <NETWORK> --mode auto
      gcloud compute firewall-rules create <NETWORK>-allow-internal \
          --network <NETWORK> --source-ranges 10.128.0.0/9 --allow all
  """

  DEFAULT_ZONE = 'us-central1-f'
  # Smallest VM allowed by API
  WORKER_MACHINE_TYPE = 'n1-standard-1'
  WORKER_DISK_SIZE = '20GB'
  # Namenode tends to fall over with less (b/26403628)
  MASTER_MACHINE_TYPE = 'n1-standard-2'
  MASTER_DISK_SIZE = '20GB'
  # Dataproc specific test network. See class docstring.
  NETWORK = 'gcloud-dataproc-test-do-not-delete'

  @property
  def messages(self):
    if self.track == calliope_base.ReleaseTrack.GA:
      return core_apis.GetMessagesModule('dataproc', 'v1')
    return core_apis.GetMessagesModule('dataproc', 'v1beta2')

  # This should let 1 failures occur without timing out the test.
  # Creating a cluster *should* take 2m, but 5m is safer.
  CREATE_TIMEOUT = '5m'

  def SetUp(self):
    """Creates a single Dataproc cluster for test methods to use."""
    self.zone = properties.VALUES.compute.zone.Get()
    if not self.zone:
      self.zone = self.DEFAULT_ZONE
    # TODO(b/36052524): Clean up clusters after beta release
    name_generator = e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-dataproc-test')
    self.cluster_name = next(name_generator)
    self.autoscaling_policy_id = next(name_generator)
    self.another_autoscaling_policy_id = next(name_generator)

  def TearDown(self):
    """Tears down the cluster."""
    try:
      self.DeleteCluster()
    except (core_exceptions.HttpException, exceptions.Error):
      # Deletion is validated in clusters_test.py. This is only a failsafe.
      pass

  def CreateCluster(self, args=''):
    result = self.RunDataproc((
        'clusters create {name} '
        '--master-machine-type {master_machine} '
        '--worker-machine-type {worker_machine} '
        '--master-boot-disk-size {master_disk_size} '
        '--worker-boot-disk-size {worker_disk_size} '
        '--num-workers 2 '
        '--network {network} '
        '--timeout {timeout} '
        '--zone {zone} '
        '{args} ').format(
            name=self.cluster_name,
            master_machine=self.MASTER_MACHINE_TYPE,
            worker_machine=self.WORKER_MACHINE_TYPE,
            master_disk_size=self.MASTER_DISK_SIZE,
            worker_disk_size=self.WORKER_DISK_SIZE,
            network=self.NETWORK,
            zone=self.zone,
            timeout=self.CREATE_TIMEOUT,
            args=args))
    self.assertEqual(self.cluster_name, result.clusterName)
    self.assertEqual(self.messages.ClusterStatus.StateValueValuesEnum.RUNNING,
                     result.status.state)
    self.assertEqual(2, result.config.workerConfig.numInstances)
    return result

  def CreateClusterWithRetries(self, max_retrials=1, args=''):
    def CleanUpFailure(result, unused_status):
      message = str(result[1][1])
      self.log.warning(
          'Cluster creation Operation failed. Details:\n' + message)
      self.DeleteCluster()
    retryer = retry.Retryer(
        max_retrials=max_retrials,
        status_update_func=CleanUpFailure)
    retryer.RetryOnException(
        self.CreateCluster,
        kwargs={'args': args},
        should_retry_if=ShouldRetryCreateCluster)

  @sdk_test_base.Retry(why='Deletion flakiness b/24265292')
  def DeleteCluster(self):
    result = self.RunDataproc(
        'clusters delete {0} -q'.format(self.cluster_name))
    self.assertTrue(result.done)
    self.assertIsNone(result.error)

  def GetSetIAMPolicy(self, group, resource_name):
    self.ClearOutput()
    self.RunDataproc('{0} get-iam-policy {1}'.format(group, resource_name),
                     output_format='json')
    policy = self.GetOutput()

    # if get was successful, the policy should contain the etag snippet.
    etag_snippet = '"etag": "'
    self.assertTrue(etag_snippet in policy)

    policy_file = self.Touch(directory=self.temp_path, contents=policy)
    self.ClearOutput()
    self.RunDataproc(
        '{0} set-iam-policy {1} {2}'.format(group, resource_name, policy_file),
        output_format='json')

    # set changes the etag, so the new policy should be different.
    self.AssertOutputNotEquals(policy, normalize_space=True)
    # but it should still contain the etag snippet.
    self.AssertOutputContains(etag_snippet)
