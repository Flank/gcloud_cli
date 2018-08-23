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

"""Base for all Dataproc unit tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import difflib

from apitools.base.py import encoding
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.resource import resource_printer_base
from tests.lib import sdk_test_base
from tests.lib.apitools import http_error
from tests.lib.surface.dataproc import base
import six


_API_VERSION = 'v1'
_BETA_API_VERSION = 'v1beta2'


class DataprocUnitTestBase(sdk_test_base.WithFakeAuth, base.DataprocTestBase):
  """Base class for all Dataproc unit tests."""

  PROJECT_NUM = 1234567890123
  CLUSTER_NAME = 'test-cluster'
  CLUSTER_UUID = '74048165-54a9-457c-b3d3-d4da3512e66b'
  CLUSTER_NAMES = ['test-cluster-0', 'test-cluster-1', 'test-cluster-2']
  GCS_BUCKET = 'test-bucket'
  OPERATION_ID = '564f9cac-e514-43e5-98de-e74442010cd3'
  REGION = 'global'
  ZONE = 'us-central1-a'
  REQUEST_ID = 'dbf5f287-f332-470b-80b2-c94b49358c45'
  WORKFLOW_TEMPLATE = 'test-workflow-template'
  WORKFLOW_TEMPLATE_IDS = [
      'test-workflow-template-0', 'test-workflow-template-1',
      'test-workflow-template-2'
  ]

  # Fake server side defaults.
  DEFAULT_NUM_WORKERS = 2
  DEFAULT_SCOPES = [
      'https://www.googleapis.com/storage.full_contol',
      'https://www.googleapis.com/actual_cloud',
  ]

  @classmethod
  def SetUpClass(cls):
    cls._messages = core_apis.GetMessagesModule('dataproc', _API_VERSION)
    cls._beta_messages = core_apis.GetMessagesModule(
        'dataproc', _BETA_API_VERSION)

  @property
  def api_version(self):
    if self.track == calliope_base.ReleaseTrack.GA:
      return _API_VERSION
    return _BETA_API_VERSION

  @property
  def messages(self):
    if self.track == calliope_base.ReleaseTrack.GA:
      return self._messages
    return self._beta_messages

  def OperationName(self, op_id=None):
    return ('projects/{project}/regions/{region}/operations/{id}'.format(
        project=self.Project(), region=self.REGION,
        id=op_id or self.OPERATION_ID))

  def ClusterUri(self):
    return ('https://dataproc.googleapis.com/{version}/projects/{project}/'
            'regions/global/clusters/test-cluster'.format(
                version=self.api_version,
                project=self.Project()))

  def ZoneUri(self):
    return 'us-central1-a'

  def SetupForReleaseTrack(self, release_track):
    self.track = release_track
    self.mock_client = mock.Client(
        core_apis.GetClientClass('dataproc', self.api_version),
        real_client=core_apis.GetClientInstance(
            'dataproc', self.api_version, no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def SetUp(self):
    self.SetupForReleaseTrack(self.track)
    # Wrap calls to WaitForOperation to set poll_period_s to 0 so
    # tests run faster.
    real_wait_for_operation = util.WaitForOperation

    def nosleep_for_operation(*args, **kwargs):
      if not kwargs:
        kwargs = {}
      kwargs.update({'poll_period_s': 0})
      return real_wait_for_operation(*args, **kwargs)
    self.StartObjectPatch(
        util, 'WaitForOperation').side_effect = nosleep_for_operation

    real_wait_for_deletion = util.WaitForResourceDeletion
    def nosleep_for_deletion(*args, **kwargs):
      if not kwargs:
        kwargs = {}
      kwargs.update({'poll_period_s': 0})
      return real_wait_for_deletion(*args, **kwargs)
    self.StartObjectPatch(
        util, 'WaitForResourceDeletion').side_effect = nosleep_for_deletion

    self.StartPatch('googlecloudsdk.api_lib.dataproc.util.GetUniqueId'
                   ).return_value = self.REQUEST_ID

  def SetOs(self, os):
    platform_patch = self.StartPatch(
        'googlecloudsdk.core.util.platforms.OperatingSystem.Current')
    platform_patch.return_value = os

  def MakeHttpError(self, status_code, message=None, failing_url=None):
    return http_error.MakeHttpError(
        status_code, message, url=failing_url or self.ClusterUri())

  def MakeRpcError(self, **kwargs):
    status_dict = {'message': 'There was an error with the operation!'}
    status_dict.update(kwargs)
    return encoding.DictToMessage(status_dict, self.messages.Status)

  def MakeOperation(self, **kwargs):
    return self.messages.Operation(
        name=kwargs.pop('name', self.OperationName()),
        done=kwargs.pop('done', False),
        error=kwargs.pop('error', None),
        response=kwargs.pop('response', None),
        metadata=encoding.DictToMessage(
            kwargs, self.messages.Operation.MetadataValue),
    )

  def MakeCompletedOperation(self, **kwargs):
    kwargs['done'] = True
    return self.MakeOperation(**kwargs)

  def MakeCluster(self, **kwargs):
    secondary_worker_config = None
    if ('secondaryWorkerConfigNumInstances' in kwargs or
        'secondaryWorkerBootDiskSizeGb' in kwargs or
        'secondaryWorkerBootDiskType' in kwargs):

      disk_config = self.messages.DiskConfig(
          bootDiskSizeGb=kwargs.get('secondaryWorkerBootDiskSizeGb', None),
          bootDiskType=kwargs.get('secondaryWorkerBootDiskType', None))

      secondary_worker_config = self.messages.InstanceGroupConfig(
          numInstances=kwargs.get('secondaryWorkerConfigNumInstances', None),
          diskConfig=disk_config)

    # Convert from a dict to Python client library version of dict (LabelsValue)
    labels = kwargs.get('labels', None)
    labels_values = None
    if labels is not None:
      labels_values = self.messages.Cluster.LabelsValue(additionalProperties=[
          self.messages.Cluster.LabelsValue.AdditionalProperty(
              key=key, value=value) for key, value in six.iteritems(labels)
      ])

    def make_disk_config(group_name):
      return self.messages.DiskConfig(
          bootDiskSizeGb=kwargs.get(group_name + 'BootDiskSizeGb', None),
          bootDiskType=kwargs.get(group_name + 'BootDiskType', None),
          numLocalSsds=kwargs.get(group_name + 'NumLocalSsds', None))

    def make_accelerators(group_name):
      type_key = group_name + 'AcceleratorTypeUri'
      count_key = group_name + 'AcceleratorCount'
      if type_key in kwargs or count_key in kwargs:
        accelerator_config = self.messages.AcceleratorConfig(
            acceleratorTypeUri=kwargs.get(type_key, None),
            acceleratorCount=kwargs.get(count_key, None))
        return [accelerator_config]
      return []

    return self.messages.Cluster(
        clusterName=kwargs.get('clusterName', self.CLUSTER_NAME),
        clusterUuid=kwargs.get('clusterUuid', None),
        labels=labels_values,
        config=kwargs.get(
            'clusterConfig',
            self.messages.ClusterConfig(
                configBucket=kwargs.get('configBucket', None),
                gceClusterConfig=kwargs.get(
                    'gceClusterConfig',
                    self.messages.GceClusterConfig(
                        networkUri=kwargs.get('networkUri', None),
                        subnetworkUri=kwargs.get('subnetworkUri', None),
                        internalIpOnly=kwargs.get('internalIpOnly', False),
                        tags=kwargs.get('tags', []),
                        metadata=kwargs.get('metadata', None),
                        serviceAccount=kwargs.get('serviceAccount', None),
                        serviceAccountScopes=kwargs.get('serviceAccountScopes',
                                                        []),
                        zoneUri=kwargs.get('zoneUri', self.ZoneUri()))),
                masterConfig=kwargs.get(
                    'masterConfig',
                    self.messages.InstanceGroupConfig(
                        numInstances=kwargs.get('masterConfigNumInstances',
                                                None),
                        imageUri=kwargs.get('imageUri', None),
                        machineTypeUri=kwargs.get('masterMachineTypeUri', None),
                        accelerators=make_accelerators('master'),
                        diskConfig=kwargs.get('masterDiskConfig',
                                              make_disk_config('master')))),
                secondaryWorkerConfig=secondary_worker_config,
                workerConfig=kwargs.get(
                    'workerConfig',
                    self.messages.InstanceGroupConfig(
                        numInstances=kwargs.get('workerConfigNumInstances',
                                                None),
                        imageUri=kwargs.get('imageUri', None),
                        machineTypeUri=kwargs.get('workerMachineTypeUri', None),
                        accelerators=make_accelerators('worker'),
                        diskConfig=kwargs.get('workerDiskConfig',
                                              make_disk_config('worker')))),
                initializationActions=kwargs.get('initializationActions', []),
                softwareConfig=self.messages.SoftwareConfig(
                    imageVersion=kwargs.get('imageVersion', None),
                    properties=kwargs.get('properties', None)))),
        projectId=kwargs.get('projectId', self.Project()),
        status=kwargs.get('status', None))

  def MakeRunningCluster(self, **kwargs):
    # Create dict of defaults set by cluster.
    running_cluster_defaults = {
        'workerConfigNumInstances': self.DEFAULT_NUM_WORKERS,
        'serviceAccountScopes': self.DEFAULT_SCOPES,
        'clusterUuid': self.CLUSTER_UUID,
        'configBucket': self.GCS_BUCKET,
        'status': self.messages.ClusterStatus(
            state=self.messages.ClusterStatus.StateValueValuesEnum.RUNNING)}
    running_cluster_defaults.update(kwargs)
    return self.MakeCluster(**running_cluster_defaults)

  # Adding min_cpu_platform separately because min_cpu_platform field is not
  # visible other than in v1beta2
  def AddMinCpuPlatform(self, cluster, master_min_cpu_platform,
                        worker_min_cpu_platform):
    cluster.config.masterConfig.minCpuPlatform = master_min_cpu_platform
    cluster.config.workerConfig.minCpuPlatform = worker_min_cpu_platform
    if cluster.config.secondaryWorkerConfig is None:
      cluster.config.secondaryWorkerConfig = self.messages.InstanceGroupConfig(
          diskConfig=self.messages.DiskConfig())
    cluster.config.secondaryWorkerConfig.minCpuPlatform = (
        worker_min_cpu_platform)

  def AddEncryptionConfig(self, cluster, kms_key):
    encryption_config = self.messages.EncryptionConfig()
    encryption_config.gcePdKmsKeyName = kms_key
    cluster.config.encryptionConfig = encryption_config

  def ExpectGetCluster(self, cluster=None, region=None, exception=None):
    if not region:
      region = self.REGION
    if not cluster:
      cluster = self.MakeRunningCluster()
      response = None
    if not exception:
      response = cluster
    self.mock_client.projects_regions_clusters.Get.Expect(
        self.messages.DataprocProjectsRegionsClustersGetRequest(
            clusterName=cluster.clusterName,
            region=region,
            projectId=cluster.projectId),
        response=response,
        exception=exception)

  def ExpectGetOperation(self, operation=None, exception=None):
    if not operation:
      operation = self.MakeOperation()
    response = None
    if not exception:
      response = operation
    self.mock_client.projects_regions_operations.Get.Expect(
        self.messages.DataprocProjectsRegionsOperationsGetRequest(
            name=operation.name),
        response=response,
        exception=exception)

  def FilterOutPageMarkers(self, resource_list):
    return [resource for resource in resource_list
            if not isinstance(resource, resource_printer_base.PageMarker)]

  # Mostly stolen from apitools.base.py.test.mock.UnexpectedRequestException
  def AssertMessagesEqual(self, expected, actual):
    if expected != actual:
      raise MessageEqualityAssertionError(expected, actual)

  def WorkflowTemplateName(self, project=None, region=None, template_id=None):
    if not project:
      project = self.Project()
    if not region:
      region = self.REGION
    if not template_id:
      template_id = self.WORKFLOW_TEMPLATE
    return 'projects/{0}/regions/{1}/workflowTemplates/{2}'.format(
        project, region, template_id)

  def WorkflowTemplateParentName(self, project=None, region=None):
    if not project:
      project = self.Project()
    if not region:
      region = self.REGION
    return 'projects/{0}/regions/{1}'.format(project, region)

  def MakeWorkflowTemplate(self,
                           name=None,
                           version=None,
                           create_time=None,
                           template_id=None,
                           labels=None,
                           update_time=None,
                           jobs=None):
    template_name = name if name else self.WorkflowTemplateName()
    template_id = template_id if template_id else self.WORKFLOW_TEMPLATE
    if not jobs:
      jobs = []

    # Convert from a dict to Python client library version of dict (LabelsValue)
    labels_values = None
    if labels:
      labels_values = self.messages.WorkflowTemplate.LabelsValue(
          additionalProperties=[
              self.messages.WorkflowTemplate.LabelsValue.AdditionalProperty(
                  key=key, value=value) for key, value in six.iteritems(labels)
          ])

    return self.messages.WorkflowTemplate(
        id=template_id,
        name=template_name,
        labels=labels_values,
        createTime=create_time,
        updateTime=update_time,
        version=version,
        jobs=jobs)

  def ExpectGetWorkflowTemplate(self,
                                name=None,
                                version=None,
                                response=None,
                                exception=None):
    if not name:
      name = self.WorkflowTemplateName()
    self.mock_client.projects_regions_workflowTemplates.Get.Expect(
        self.messages.DataprocProjectsRegionsWorkflowTemplatesGetRequest(
            name=name, version=version),
        response=response,
        exception=exception)


class DataprocIAMUnitTestBase(DataprocUnitTestBase):
  """Base test class for all Dataproc IAM unit tests."""

  CLUSTER = 'cluster'
  JOB = 'job'
  OPERATION = 'operation'
  TEMPLATE = 'workflow-template'

  def GetTestIamPolicy(self, clear_fields=None):
    """Creates a test IAM policy.

    Args:
        clear_fields: list of policy fields to clear.
    Returns:
        IAM policy.
    """
    if clear_fields is None:
      clear_fields = []

    policy = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                members=[
                    'serviceAccount:123hash@developer.gserviceaccount.com'
                ],
                role='roles/editor'),
            self.messages.Binding(
                members=['user:tester@gmail.com', 'user:slick@gmail.com'],
                role='roles/owner')
        ],
        etag=b'<< Unique versioning etag bytefield >>',
        version=0)

    for field in clear_fields:
      policy.reset(field)

    return policy

  def RelativeName(self, collection):
    fmt = 'projects/{project}/regions/global/'
    if collection == self.CLUSTER:
      fmt += 'clusters/test-{collection}'
    elif collection == self.JOB:
      fmt += 'jobs/test-{collection}'
    elif collection == self.OPERATION:
      fmt += 'operations/test-operation'
    elif collection == self.TEMPLATE:
      fmt += 'workflowTemplates/test-{collection}'
    else:
      raise ValueError('Invalid collection')

    return fmt.format(project=self.Project(), collection=collection)

  def MockedService(self, collection):
    if collection == self.CLUSTER:
      return self.mock_client.projects_regions_clusters
    elif collection == self.JOB:
      return self.mock_client.projects_regions_jobs
    elif collection == self.OPERATION:
      return self.mock_client.projects_regions_operations
    elif collection == self.TEMPLATE:
      return self.mock_client.projects_regions_workflowTemplates
    else:
      raise ValueError('Invalid collection')

  def GetIAMPolicyMessageClass(self, collection):
    if collection == self.CLUSTER:
      return self.messages.DataprocProjectsRegionsClustersGetIamPolicyRequest
    elif collection == self.JOB:
      return self.messages.DataprocProjectsRegionsJobsGetIamPolicyRequest
    elif collection == self.OPERATION:
      return self.messages.DataprocProjectsRegionsOperationsGetIamPolicyRequest
    elif collection == self.TEMPLATE:
      # pylint: disable=line-too-long
      return self.messages.DataprocProjectsRegionsWorkflowTemplatesGetIamPolicyRequest
      # pylint: enable=line-too-long
    else:
      raise ValueError('Invalid collection')

  def SetIAMPolicyMessageClass(self, collection):
    if collection == self.CLUSTER:
      return self.messages.DataprocProjectsRegionsClustersSetIamPolicyRequest
    elif collection == self.JOB:
      return self.messages.DataprocProjectsRegionsJobsSetIamPolicyRequest
    elif collection == self.OPERATION:
      return self.messages.DataprocProjectsRegionsOperationsSetIamPolicyRequest
    elif collection == self.TEMPLATE:
      # pylint: disable=line-too-long
      return self.messages.DataprocProjectsRegionsWorkflowTemplatesSetIamPolicyRequest
      # pylint: enable=line-too-long
    else:
      raise ValueError('Invalid collection')


class MessageEqualityAssertionError(AssertionError):
  """Extend AssertionError with difference between two protos in message."""

  def __init__(self, expected, actual):
    expected_repr = encoding.MessageToRepr(expected, multiline=True)
    actual_repr = encoding.MessageToRepr(actual, multiline=True)

    expected_lines = expected_repr.splitlines()
    actual_lines = actual_repr.splitlines()

    diff_lines = difflib.unified_diff(expected_lines, actual_lines)

    message = '\n'.join(
        ['expected: {expected}', 'actual: {actual}', 'diff:']
        + list(diff_lines)).format(expected=expected_repr, actual=actual_repr)
    super(MessageEqualityAssertionError, self).__init__(message)
