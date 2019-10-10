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

"""Test of the 'clusters update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import unit_base
import six


class ClustersUpdateUnitTest(unit_base.DataprocUnitTestBase):
  """Tests for dataproc clusters update."""

  def ExpectUpdateCluster(
      self, cluster, field_paths, graceful_decommission_timeout=None,
      response=None, exception=None):
    if not (response or exception):
      response = self.MakeOperation()

    self.mock_client.projects_regions_clusters.Patch.Expect(
        self.messages.DataprocProjectsRegionsClustersPatchRequest(
            clusterName=cluster.clusterName,
            projectId=self.Project(),
            region=self.REGION,
            cluster=cluster,
            gracefulDecommissionTimeout=graceful_decommission_timeout,
            updateMask=','.join(field_paths),
            requestId=self.REQUEST_ID),
        response=response,
        exception=exception)

  def ExpectUpdateCalls(self, cluster, field_paths,
                        graceful_decommission_timeout=None, response=None,
                        error=None):
    # Update cluster returns operation pending
    self.ExpectUpdateCluster(
        cluster=cluster,
        field_paths=field_paths,
        graceful_decommission_timeout=graceful_decommission_timeout)
    # Initial get operation returns pending
    self.ExpectGetOperation()
    # Second get operation returns done
    self.ExpectGetOperation(operation=self.MakeCompletedOperation(error=error))
    if not error:
      # Get the cluster to display it.
      self.ExpectGetCluster(cluster=response)

  def testUpdateClusterPrimaryWorkers(self):
    cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        config=self.messages.ClusterConfig(
            workerConfig=self.messages.InstanceGroupConfig(numInstances=10)))
    expected = self.MakeRunningCluster(workerConfigNumInstances=10)
    changed_fields = ['config.worker_config.num_instances']
    self.ExpectUpdateCalls(
        cluster=cluster, field_paths=changed_fields, response=expected)
    result = self.RunDataproc(
        'clusters update {0} --num-workers 10'.format(self.CLUSTER_NAME))
    self.AssertMessagesEqual(expected, result)

  def testUpdateClusterSecondaryWorkers(self):
    cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        config=self.messages.ClusterConfig(
            secondaryWorkerConfig=self.messages.InstanceGroupConfig(
                numInstances=5)))
    expected = self.MakeRunningCluster(
        secondaryWorkerConfigNumInstances=5)
    changed_fields = [
        'config.secondary_worker_config.num_instances']
    self.ExpectUpdateCalls(
        cluster=cluster, field_paths=changed_fields, response=expected)
    result = self.RunDataproc(
        'clusters update {0} '
        '--num-preemptible-workers 5'.format(self.CLUSTER_NAME))
    self.AssertMessagesEqual(expected, result)

  def testUpdateClearLabels(self):
    cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        config=self.messages.ClusterConfig(),
        labels=self.messages.Cluster.LabelsValue(additionalProperties=[]))
    orig_cluster = self.MakeRunningCluster(labels={'key': 'value'})
    self.ExpectGetCluster(orig_cluster)
    changed_fields = ['labels']
    self.ExpectUpdateCalls(
        cluster=cluster, field_paths=changed_fields, response=cluster)
    result = self.RunDataproc(
        'clusters update {0} '
        '--clear-labels'.format(self.CLUSTER_NAME))
    self.AssertMessagesEqual(cluster, result)

  def testUpdateClusterAllOptions(self):
    orig_cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        labels=self.labelsDictToMessage({
            'customer': 'emca',
            'accident': 'oops'
        }),
        config=self.messages.ClusterConfig(
            workerConfig=self.messages.InstanceGroupConfig(numInstances=10),
            secondaryWorkerConfig=self.messages.InstanceGroupConfig(
                numInstances=5)))
    updated_cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        labels=self.labelsDictToMessage({
            'customer': 'acme',
            'keyonly': ''
        }),
        config=self.messages.ClusterConfig(
            workerConfig=self.messages.InstanceGroupConfig(numInstances=10),
            secondaryWorkerConfig=self.messages.InstanceGroupConfig(
                numInstances=5)))
    self.ExpectGetCluster(orig_cluster)
    changed_fields = [
        'config.worker_config.num_instances',
        'config.secondary_worker_config.num_instances',
        'labels']
    expected = self.MakeRunningCluster(
        labels={'customer': 'acme', 'keyonly': ''},
        secondaryWorkerConfigNumInstances=5,
        workerConfigNumInstances=10)
    self.ExpectUpdateCalls(
        cluster=updated_cluster, field_paths=changed_fields, response=expected)
    result = self.RunDataproc(
        'clusters update {0} '
        '--update-labels=customer=acme,keyonly="" '
        '--remove-labels=accident '
        '--num-workers 10 '
        '--num-preemptible-workers 5'.format(self.CLUSTER_NAME))
    self.AssertMessagesEqual(expected, result)

  def testUpdateClusterOperationFailure(self):
    cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        config=self.messages.ClusterConfig(
            workerConfig=self.messages.InstanceGroupConfig(numInstances=10)))
    changed_fields = ['config.worker_config.num_instances']
    self.ExpectUpdateCalls(
        cluster=cluster, field_paths=changed_fields, error=self.MakeRpcError())
    with self.AssertRaisesExceptionMatches(
        exceptions.OperationError,
        'Operation [{0}] failed: There was an error with the operation!'.format(
            self.OperationName())):
      self.RunDataproc(
          'clusters update {0} --num-workers 10'.format(self.CLUSTER_NAME))

  def testUpdateClusterNotFound(self):
    cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        config=self.messages.ClusterConfig(
            workerConfig=self.messages.InstanceGroupConfig(numInstances=10)))
    changed_fields = ['config.worker_config.num_instances']
    self.ExpectUpdateCluster(
        cluster=cluster,
        field_paths=changed_fields,
        exception=self.MakeHttpError(404))
    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: Resource not found.'):
      self.RunDataproc(
          'clusters update {0} --num-workers 10'.format(self.CLUSTER_NAME))

  def testUpdateClustersAsync(self):
    cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        config=self.messages.ClusterConfig(
            workerConfig=self.messages.InstanceGroupConfig(numInstances=10)))
    changed_fields = ['config.worker_config.num_instances']
    self.ExpectUpdateCluster(
        cluster=cluster, field_paths=changed_fields)
    self.RunDataproc(
        'clusters update {0} --num-workers 10 --async'.format(
            self.CLUSTER_NAME))
    self.AssertErrContains('Updating [{0}] with operation [{1}].'.format(
        self.ClusterUri(), self.OperationName()))

  def testUpdateClusterUpdateLabels(self):
    orig_cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        labels=self.labelsDictToMessage({
            'customer': 'orig_acme'
        }),
        projectId=self.Project(),
        config=self.messages.ClusterConfig())
    updated_cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        labels=self.labelsDictToMessage({
            'customer': 'acme'
        }),
        projectId=self.Project(),
        config=self.messages.ClusterConfig())
    self.ExpectGetCluster(orig_cluster)
    expected = self.MakeRunningCluster(labels={'customer': 'acme'})
    changed_fields = ['labels']
    self.ExpectUpdateCalls(
        cluster=updated_cluster, field_paths=changed_fields, response=expected)
    result = self.RunDataproc(
        'clusters update {0} --update-labels=customer=acme'.format(
            self.CLUSTER_NAME))
    self.AssertMessagesEqual(expected, result)

  def testUpdateClusterAddLabels(self):
    orig_cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        labels=self.labelsDictToMessage({
            'customer': 'acme'
        }),
        projectId=self.Project(),
        config=self.messages.ClusterConfig())
    updated_cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        labels=self.labelsDictToMessage({
            'customer': 'acme',
            'size': 'big'
        }),
        projectId=self.Project(),
        config=self.messages.ClusterConfig())
    self.ExpectGetCluster(orig_cluster)
    expected = self.MakeRunningCluster(
        labels={'customer': 'acme', 'size': 'big'})
    changed_fields = ['labels']
    self.ExpectUpdateCalls(
        cluster=updated_cluster, field_paths=changed_fields, response=expected)
    result = self.RunDataproc(
        'clusters update {0} --update-labels=size=big'.format(
            self.CLUSTER_NAME))
    self.AssertMessagesEqual(expected, result)

  def testUpdateClusterRemoveLabels(self):
    orig_cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        labels=self.labelsDictToMessage({
            'customer': 'acme',
            'size': 'big'
        }),
        projectId=self.Project(),
        config=self.messages.ClusterConfig())
    updated_cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        labels=self.labelsDictToMessage({
            'customer': 'acme'
        }),
        projectId=self.Project(),
        config=self.messages.ClusterConfig())
    self.ExpectGetCluster(orig_cluster)
    expected = self.MakeRunningCluster(labels={'customer': 'acme'})
    changed_fields = ['labels']
    self.ExpectUpdateCalls(
        cluster=updated_cluster, field_paths=changed_fields, response=expected)
    result = self.RunDataproc(
        'clusters update {0} --remove-labels=size'.format(self.CLUSTER_NAME))
    self.AssertMessagesEqual(expected, result)

  def testUpdateClusterPrimaryWorkersHiddenFlags(self):
    cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        config=self.messages.ClusterConfig(
            workerConfig=self.messages.InstanceGroupConfig(numInstances=10)))
    expected = self.MakeRunningCluster(workerConfigNumInstances=10)
    changed_fields = ['config.worker_config.num_instances']
    self.ExpectUpdateCalls(
        cluster=cluster, field_paths=changed_fields, response=expected)
    result = self.RunDataproc((
        'clusters update {0} '
        '--num-workers 10 '
        '--timeout 42s'
    ).format(self.CLUSTER_NAME))
    self.AssertMessagesEqual(expected, result)

  def testUpdateClusterNoOperationGetPermission(self):
    operation = self.MakeOperation()
    cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        config=self.messages.ClusterConfig(
            workerConfig=self.messages.InstanceGroupConfig(numInstances=10)))
    changed_fields = ['config.worker_config.num_instances']

    self.ExpectUpdateCluster(
        cluster=cluster, field_paths=changed_fields, response=operation)

    self.ExpectGetOperation(
        operation=operation,
        exception=self.MakeHttpError(403))

    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc((
          'clusters update {0} '
          '--num-workers 10'
      ).format(self.CLUSTER_NAME))

  def labelsDictToMessage(self, labels_dict):
    return self.messages.Cluster.LabelsValue(additionalProperties=[
        self.messages.Cluster.LabelsValue.AdditionalProperty(
            key=key, value=value)
        for key, value in sorted(six.iteritems(labels_dict))
    ])

  def testUpdateCluster_withGracefulDecommissionTimeout(self):
    cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        config=self.messages.ClusterConfig(
            workerConfig=self.messages.InstanceGroupConfig(numInstances=10)))
    expected = self.MakeRunningCluster(workerConfigNumInstances=10,
                                       gracefulDecommissionTimeout='100s')
    changed_fields = ['config.worker_config.num_instances']
    self.ExpectUpdateCalls(
        cluster=cluster, field_paths=changed_fields,
        graceful_decommission_timeout='100s', response=expected)
    result = self.RunDataproc(
        ('clusters update {0} --num-workers 10 '
         '--graceful-decommission-timeout 100s').format(self.CLUSTER_NAME))
    self.AssertMessagesEqual(expected, result)

  def testUpdateCluster_withNegativeGracefulDecommissionTimeout(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        ('argument --graceful-decommission-timeout: value must be greater than '
         'or equal to 0s; received: -100s')):
      self.RunDataproc(
          ('clusters update {0} --num-workers 10 '
           '--graceful-decommission-timeout=-100s').format(self.CLUSTER_NAME))

  def testUpdateCluster_withLargeGracefulDecommissionTimeout(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        ('argument --graceful-decommission-timeout: value must be less than or '
         'equal to 1d; received: 2d')):
      self.RunDataproc(
          ('clusters update {0} --num-workers 10 '
           '--graceful-decommission-timeout=2d').format(self.CLUSTER_NAME))

  def testUpdateCluster_withMaxAgeAndMaxIdle(self):
    cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        config=self.messages.ClusterConfig(
            lifecycleConfig=self.messages.LifecycleConfig(
                idleDeleteTtl='700s', autoDeleteTtl='1300s')))
    expected = self.MakeRunningCluster()
    expected.config.lifecycleConfig = self.messages.LifecycleConfig(
        autoDeleteTtl='1300s', idleDeleteTtl='700s')
    changed_fields = [
        'config.lifecycle_config.auto_delete_ttl',
        'config.lifecycle_config.idle_delete_ttl'
    ]
    self.ExpectUpdateCalls(
        cluster=cluster, field_paths=changed_fields, response=expected)
    result = self.RunDataproc(
        ('clusters update {0} --max-age "1300s" --max-idle "700s"'
        ).format(self.CLUSTER_NAME))
    self.AssertMessagesEqual(expected, result)

  def testUpdateCluster_withExpirationTimeAndMaxIdle(self):
    cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        config=self.messages.ClusterConfig(
            lifecycleConfig=self.messages.LifecycleConfig(
                idleDeleteTtl='700s',
                autoDeleteTime='2017-08-29T18:52:51.142Z')))
    expected = self.MakeRunningCluster()
    expected.config.lifecycleConfig = self.messages.LifecycleConfig(
        autoDeleteTime='2017-08-29T18:52:51.142Z', idleDeleteTtl='700s')
    changed_fields = [
        'config.lifecycle_config.auto_delete_time',
        'config.lifecycle_config.idle_delete_ttl'
    ]
    self.ExpectUpdateCalls(
        cluster=cluster, field_paths=changed_fields, response=expected)
    result = self.RunDataproc(
        ('clusters update {0} --expiration-time "2017-08-29T18:52:51.142Z" '
         '--max-idle "700s"').format(self.CLUSTER_NAME))
    self.AssertMessagesEqual(expected, result)

  def testUpdateCluster_withMaxAgeAndNoMaxIdle(self):
    cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        config=self.messages.ClusterConfig(
            lifecycleConfig=self.messages.LifecycleConfig(
                autoDeleteTtl='700s', idleDeleteTtl=None)))
    expected = self.MakeRunningCluster()
    expected.config.lifecycleConfig = self.messages.LifecycleConfig(
        autoDeleteTtl='700s', idleDeleteTtl=None)
    changed_fields = [
        'config.lifecycle_config.auto_delete_ttl',
        'config.lifecycle_config.idle_delete_ttl'
    ]
    self.ExpectUpdateCalls(
        cluster=cluster, field_paths=changed_fields, response=expected)
    result = self.RunDataproc(
        ('clusters update {0} --max-age "700s" --no-max-idle '
        ).format(self.CLUSTER_NAME))
    self.AssertMessagesEqual(expected, result)

  def testUpdateCluster_withNoMaxAgeAndNoMaxIdle(self):
    cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        config=self.messages.ClusterConfig(
            lifecycleConfig=self.messages.LifecycleConfig(
                autoDeleteTtl=None, idleDeleteTtl=None)))
    expected = self.MakeRunningCluster()
    expected.config.lifecycleConfig = self.messages.LifecycleConfig(
        autoDeleteTtl=None, idleDeleteTtl=None)
    changed_fields = [
        'config.lifecycle_config.auto_delete_ttl',
        'config.lifecycle_config.idle_delete_ttl'
    ]
    self.ExpectUpdateCalls(
        cluster=cluster, field_paths=changed_fields, response=expected)
    result = self.RunDataproc(
        ('clusters update {0} --no-max-age --no-max-idle ').format(
            self.CLUSTER_NAME))
    self.AssertMessagesEqual(expected, result)

  # This tests enabling autoscaling and switching policies, since they have
  # equivalent client-side behavior.
  def testUpdateCluster_enableAutoscaling_onlyId(self):
    specified_policy = 'cool-policy'
    expected_policy_uri = 'projects/fake-project/regions/global/autoscalingPolicies/cool-policy'

    cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        config=self.messages.ClusterConfig(
            autoscalingConfig=self.messages.AutoscalingConfig(
                policyUri=expected_policy_uri)))
    expected = self.MakeRunningCluster()
    expected.config.autoscalingConfig = self.messages.AutoscalingConfig(
        policyUri=expected_policy_uri)
    changed_fields = [
        'config.autoscaling_config.policy_uri',
    ]
    self.ExpectUpdateCalls(
        cluster=cluster, field_paths=changed_fields, response=expected)
    result = self.RunDataproc(
        ('clusters update {0} --autoscaling-policy {1} ').format(
            self.CLUSTER_NAME, specified_policy))
    self.AssertMessagesEqual(expected, result)

  def testUpdateCluster_enableAutoscaling_uriInDifferentProjectAndRegion(self):
    specified_policy = 'projects/another-project/regions/another-region/autoscalingPolicies/cool-policy'

    cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        config=self.messages.ClusterConfig(
            autoscalingConfig=self.messages.AutoscalingConfig(
                policyUri=specified_policy)))
    expected = self.MakeRunningCluster()
    expected.config.autoscalingConfig = self.messages.AutoscalingConfig(
        policyUri=specified_policy)
    changed_fields = [
        'config.autoscaling_config.policy_uri',
    ]
    self.ExpectUpdateCalls(
        cluster=cluster, field_paths=changed_fields, response=expected)
    result = self.RunDataproc(
        ('clusters update {0} --autoscaling-policy {1} ').format(
            self.CLUSTER_NAME, specified_policy))
    self.AssertMessagesEqual(expected, result)

  def testUpdateCluster_enableAutoscaling_fullUrl(self):
    # Only sends the part starting with projects/
    specified_policy = 'https://dataproc.googleapis.com/v1beta2/projects/fake-project/regions/global/autoscalingPolicies/cool-policy'
    expected_policy_uri = 'projects/fake-project/regions/global/autoscalingPolicies/cool-policy'

    cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        config=self.messages.ClusterConfig(
            autoscalingConfig=self.messages.AutoscalingConfig(
                policyUri=expected_policy_uri)))
    expected = self.MakeRunningCluster()
    expected.config.autoscalingConfig = self.messages.AutoscalingConfig(
        policyUri=expected_policy_uri)
    changed_fields = [
        'config.autoscaling_config.policy_uri',
    ]
    self.ExpectUpdateCalls(
        cluster=cluster, field_paths=changed_fields, response=expected)
    result = self.RunDataproc(
        ('clusters update {0} --autoscaling-policy {1} ').format(
            self.CLUSTER_NAME, specified_policy))
    self.AssertMessagesEqual(expected, result)

  def testUpdateCluster_disableAutoscaling_emptyPolicy(self):
    cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        config=self.messages.ClusterConfig(autoscalingConfig=None))
    expected = self.MakeRunningCluster()
    expected.config.autoscalingConfig = None
    changed_fields = [
        'config.autoscaling_config.policy_uri',
    ]
    self.ExpectUpdateCalls(
        cluster=cluster, field_paths=changed_fields, response=expected)
    result = self.RunDataproc(
        ('clusters update {0} --autoscaling-policy=').format(self.CLUSTER_NAME))
    self.AssertMessagesEqual(expected, result)

  def testUpdateCluster_disableAutoscaling_withDisableFlag(self):
    cluster = self.messages.Cluster(
        clusterName=self.CLUSTER_NAME,
        projectId=self.Project(),
        config=self.messages.ClusterConfig(autoscalingConfig=None))
    expected = self.MakeRunningCluster()
    expected.config.autoscalingConfig = None
    changed_fields = [
        'config.autoscaling_config.policy_uri',
    ]
    self.ExpectUpdateCalls(
        cluster=cluster, field_paths=changed_fields, response=expected)
    result = self.RunDataproc(
        ('clusters update {0} --disable-autoscaling').format(self.CLUSTER_NAME))
    self.AssertMessagesEqual(expected, result)


class ClustersUpdateUnitTestBeta(ClustersUpdateUnitTest,
                                 base.DataprocTestBaseBeta):
  """Tests for dataproc clusters update."""

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)

  def testUpdateCluster_withExpirationTimeAndMaxAge(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --expiration-time: At most one of --expiration-time | '
        '--max-age | --no-max-age may be specified.'
    ):
      self.RunDataproc(
          ('clusters update {0} --expiration-time "2017-08-29T18:52:51.142Z" '
           '--max-age "700s"').format(self.CLUSTER_NAME))

  def testUpdateCluster_withExpirationTimeAndNoMaxAge(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --expiration-time: At most one of --expiration-time | '
        '--max-age | --no-max-age may be specified.'):
      self.RunDataproc(
          ('clusters update {0} --expiration-time "2017-08-29T18:52:51.142Z" '
           '--no-max-age ').format(self.CLUSTER_NAME))

  def testUpdateCluster_withMaxIdleAndNoMaxIdle(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --max-idle: At most one of --max-idle | --no-max-idle may be'
        ' specified.'
    ):
      self.RunDataproc(('clusters update {0} --max-idle "1300s" '
                        '--no-max-idle ').format(self.CLUSTER_NAME))

  def testUpdateCluster_withExpirationTimeIncorrectDatetimeFormat(self):
    with self.AssertRaisesArgumentErrorRegexp(
        'argument --expiration-time: Failed to parse date/time: bad month '
        'number 22; must be 1-12; received: 2017-22T13:31:48-08:00'
    ):
      self.RunDataproc(
          ('clusters update {0} --expiration-time=2017-22T13:31:48-08:00'
          ).format(self.CLUSTER_NAME))


class ClustersUpdateUnitTestAlpha(
    ClustersUpdateUnitTestBeta, base.DataprocTestBaseAlpha):
  pass


if __name__ == '__main__':
  sdk_test_base.main()
