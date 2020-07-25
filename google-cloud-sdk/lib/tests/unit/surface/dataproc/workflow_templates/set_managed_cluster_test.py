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
"""Test of the 'workflow-template set-managed-cluster' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import copy

from apitools.base.py import encoding

from googlecloudsdk import calliope
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.core import properties
from tests.lib.surface.dataproc import compute_base
from tests.lib.surface.dataproc import unit_base


class WorkflowTemplateSetManagedClusterUnitTest(
    unit_base.DataprocUnitTestBase, compute_base.BaseComputeUnitTest):
  """Tests for dataproc workflow-template set-managed-cluster."""

  def MakeManagedCluster(self, **kwargs):
    cluster = self.MakeCluster(**kwargs)
    return self.messages.ManagedCluster(
        clusterName=cluster.clusterName,
        config=cluster.config,
        labels=cluster.labels)

  def ExpectSetManagedCluster(self,
                              workflow_template=None,
                              response=None,
                              exception=None):
    if not (response or exception):
      response = copy.deepcopy(workflow_template)
    self.mock_client.projects_regions_workflowTemplates.Update.Expect(
        workflow_template, response=response, exception=exception)

  def ExpectCallSetManagedCluster(self,
                                  workflow_template=None,
                                  managed_cluster=None,
                                  region=None,
                                  response=None,
                                  exception=None):
    if not workflow_template:
      workflow_template = self.MakeWorkflowTemplate(region=region)
    self.ExpectGetWorkflowTemplate(
        name=workflow_template.name,
        version=workflow_template.version,
        region=region,
        response=workflow_template)
    if not managed_cluster:
      cluster_name = 'test-cluster'
      managed_cluster = self.MakeManagedCluster(clusterName=cluster_name)
    workflow_template.placement = self.messages.WorkflowTemplatePlacement(
        managedCluster=managed_cluster)
    if not (response or exception):
      response = copy.deepcopy(workflow_template)
    self.ExpectSetManagedCluster(
        workflow_template, response=response, exception=exception)

  def _testSetManagedCluster(self, region=None, region_flag=''):
    if region is None:
      region = self.REGION
    workflow_template = self.MakeWorkflowTemplate(region=region)
    cluster_name = 'test-cluster'
    managed_cluster = self.MakeManagedCluster(
        clusterName=cluster_name,
        zoneUri='us-west1-a',
        mainMachineTypeUri='n1-standard-2',
        workerConfigNumInstances=2)
    self.ExpectCallSetManagedCluster(
        workflow_template=workflow_template,
        managed_cluster=managed_cluster,
        region=region)
    result = self.RunDataproc('workflow-templates set-managed-cluster {0} '
                              '--cluster-name {1} '
                              '--zone us-west1-a --num-workers 2 '
                              '--main-machine-type n1-standard-2'
                              ' {2}'.format(
                                  self.WORKFLOW_TEMPLATE,
                                  cluster_name,
                                  region_flag))
    self.AssertMessagesEqual(workflow_template, result)

  def testSetManagedCluster(self):
    self._testSetManagedCluster()

  def testSetManagedCluster_regionProperty(self):
    properties.VALUES.dataproc.region.Set('global')
    self._testSetManagedCluster(region='global')

  def testSetManagedCluster_region_flag(self):
    properties.VALUES.dataproc.region.Set('global')
    self._testSetManagedCluster(
        region='us-central1', region_flag='--region=us-central1')

  def testSetManagedCluster_withoutRegionProperty(self):
    # No region is specified via flag or config.
    regex = r'Failed to find attribute \[region\]'
    with self.assertRaisesRegex(handlers.ParseError, regex):
      self.RunDataproc('workflow-templates set-managed-cluster foo '
                       '--cluster-name bar', set_region=False)

  def testSetManagedClusterFlags(self):
    cluster_name = 'test-cluster'
    zone = 'foo-zone'
    main_machine_type = 'foo-type'
    worker_machine_type = 'bar-type'
    bucket = 'foo-bucket'
    num_mains = 3
    num_workers = 7
    num_secondary_workers = 5
    image_version = '1.7'
    network = 'foo-network'
    network_uri = ('https://compute.googleapis.com/compute/v1/projects/'
                   'fake-project/global/networks/foo-network')
    action_uris = ['gs://my-bucket/action1.sh', 'gs://my-bucket/action2.sh']
    initialization_actions = [
        self.messages.NodeInitializationAction(
            executableFile=action_uris[0], executionTimeout='120s'),
        self.messages.NodeInitializationAction(
            executableFile=action_uris[1], executionTimeout='120s')
    ]
    service_account = 'test-account'
    scope_list = 'https://www.googleapis.com/auth/dataproc-stuff,cloud-platform'
    scope_uris = [
        'https://www.googleapis.com/auth/cloud-platform',
        'https://www.googleapis.com/auth/dataproc-stuff',
    ]
    cluster_properties = collections.OrderedDict([
        ('core:com.foo', 'foo'),
        ('hdfs:com.bar', 'bar')])
    cluster_metadata = collections.OrderedDict([
        ('key1', 'value1'),
        ('key2', 'value2')])

    managed_cluster = self.MakeManagedCluster(
        clusterName=cluster_name,
        configBucket=bucket,
        imageVersion=image_version,
        mainMachineTypeUri=main_machine_type,
        workerMachineTypeUri=worker_machine_type,
        networkUri=network_uri,
        mainConfigNumInstances=num_mains,
        workerConfigNumInstances=num_workers,
        secondaryWorkerConfigNumInstances=num_secondary_workers,
        zoneUri=zone,
        initializationActions=initialization_actions,
        serviceAccount=service_account,
        serviceAccountScopes=scope_uris,
        properties=encoding.DictToAdditionalPropertyMessage(
            cluster_properties, self.messages.SoftwareConfig.PropertiesValue),
        tags=['tag1', 'tag2'],
        metadata=encoding.DictToAdditionalPropertyMessage(
            cluster_metadata, self.messages.GceClusterConfig.MetadataValue))

    workflow_template = self.MakeWorkflowTemplate()
    self.ExpectCallSetManagedCluster(
        workflow_template=workflow_template, managed_cluster=managed_cluster)

    command = ('workflow-templates set-managed-cluster {template} '
               '--cluster-name {cluster_name} '
               '--bucket {bucket} '
               '--zone {zone} '
               '--num-mains {num_mains} '
               '--num-workers {num_workers} '
               '--main-machine-type {main_machine_type} '
               '--worker-machine-type {worker_machine_type} '
               '--network {network} '
               '--image-version {image_version} '
               '--initialization-action-timeout 2m '
               '--initialization-actions {actions} '
               '--num-secondary-workers {num_secondary} '
               '--service-account {service_account} '
               '--scopes {scopes} '
               '--properties core:com.foo=foo,hdfs:com.bar=bar '
               '--tags tag1,tag2 '
               '--metadata key1=value1,key2=value2 ').format(
                   template=self.WORKFLOW_TEMPLATE,
                   cluster_name=cluster_name,
                   bucket=bucket,
                   zone=zone,
                   num_mains=num_mains,
                   num_workers=num_workers,
                   main_machine_type=main_machine_type,
                   worker_machine_type=worker_machine_type,
                   network=network,
                   image_version=image_version,
                   actions=','.join(action_uris),
                   num_secondary=num_secondary_workers,
                   service_account=service_account,
                   scopes=scope_list)

    result = self.RunDataproc(command)
    self.AssertMessagesEqual(workflow_template, result)

  def testSetManagedClusterAutoZone(self):
    properties.VALUES.dataproc.region.Set('us-test1')
    template_name = self.WorkflowTemplateName(region='us-test1')
    cluster_name = 'test-cluster'
    workflow_template = self.MakeWorkflowTemplate(name=template_name)
    managed_cluster = self.MakeManagedCluster(
        clusterName=cluster_name, region='us-test1', zoneUri='')
    self.ExpectCallSetManagedCluster(
        workflow_template=workflow_template, managed_cluster=managed_cluster)
    result = self.RunDataproc(
        'workflow-templates set-managed-cluster {template} '
        '--cluster-name {cluster_name} '
        '--zone=""'.format(
            template=workflow_template.id, cluster_name=cluster_name))
    self.AssertMessagesEqual(workflow_template, result)
    self.AssertErrEquals('')

  def testSetManagedClusterNoName(self):
    workflow_template = self.MakeWorkflowTemplate()
    project = self.Project()
    zone = 'foo-zone'
    managed_cluster = self.MakeManagedCluster(
        clusterName=workflow_template.id, projectId=project, zoneUri=zone)
    self.ExpectCallSetManagedCluster(
        workflow_template=workflow_template, managed_cluster=managed_cluster)

    result = self.RunDataproc(
        'workflow-templates set-managed-cluster {template} '
        '--zone {zone}'.format(template=workflow_template.id, zone=zone))
    self.AssertMessagesEqual(workflow_template, result)

  def testSetManagedClusterOmitZone_globalRegion(self):
    self.MockCompute()
    self.ExpectListZones()
    self.WriteInput('3\n')  # antarctica-north42-a

    template_name = self.WorkflowTemplateName(region='global')
    cluster_name = 'test-cluster'
    workflow_template = self.MakeWorkflowTemplate(name=template_name)
    managed_cluster = self.MakeManagedCluster(
        clusterName=cluster_name, zoneUri='')
    self.ExpectCallSetManagedCluster(
        workflow_template=workflow_template, managed_cluster=managed_cluster)
    result = self.RunDataproc(
        'workflow-templates set-managed-cluster {template} '
        '--cluster-name {cluster_name} '
        '--region {region} '
        '--zone=""'.format(
            template=workflow_template.id,
            cluster_name=cluster_name,
            region='global'),
        set_region=False)
    self.AssertMessagesEqual(workflow_template, result)
    self.AssertErrContains('PROMPT_CHOICE')
    self.AssertErrContains(
        '"choices": ["antarctica-north42-a (DEPRECATED)", '
        '"antarctica-north42-b", "europe-west1-a", "europe-west1-b (DELETED)"]')


class WorkflowTemplateSetManagedClusterUnitTestBeta(
    WorkflowTemplateSetManagedClusterUnitTest):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.BETA

  def testSetManagedClusterFlags(self):
    cluster_name = 'test-cluster'
    zone = 'foo-zone'
    main_machine_type = 'foo-type'
    worker_machine_type = 'bar-type'
    bucket = 'foo-bucket'
    num_mains = 3
    num_workers = 7
    num_secondary_workers = 5
    image_version = '1.7'
    network = 'foo-network'
    network_uri = ('https://compute.googleapis.com/compute/beta/projects/'
                   'fake-project/global/networks/foo-network')
    action_uris = ['gs://my-bucket/action1.sh', 'gs://my-bucket/action2.sh']
    initialization_actions = [
        self.messages.NodeInitializationAction(
            executableFile=action_uris[0], executionTimeout='120s'),
        self.messages.NodeInitializationAction(
            executableFile=action_uris[1], executionTimeout='120s')
    ]
    service_account = 'test-account'
    scope_list = 'https://www.googleapis.com/auth/dataproc-stuff,cloud-platform'
    scope_uris = [
        'https://www.googleapis.com/auth/cloud-platform',
        'https://www.googleapis.com/auth/dataproc-stuff',
    ]
    cluster_properties = collections.OrderedDict([
        ('core:com.foo', 'foo'),
        ('hdfs:com.bar', 'bar')])
    cluster_metadata = collections.OrderedDict([
        ('key1', 'value1'),
        ('key2', 'value2')])
    managed_cluster = self.MakeManagedCluster(
        clusterName=cluster_name,
        configBucket=bucket,
        imageVersion=image_version,
        mainMachineTypeUri=main_machine_type,
        workerMachineTypeUri=worker_machine_type,
        networkUri=network_uri,
        mainConfigNumInstances=num_mains,
        workerConfigNumInstances=num_workers,
        secondaryWorkerConfigNumInstances=num_secondary_workers,
        zoneUri=zone,
        initializationActions=initialization_actions,
        serviceAccount=service_account,
        serviceAccountScopes=scope_uris,
        properties=encoding.DictToAdditionalPropertyMessage(
            cluster_properties, self.messages.SoftwareConfig.PropertiesValue),
        tags=['tag1', 'tag2'],
        metadata=encoding.DictToAdditionalPropertyMessage(
            cluster_metadata, self.messages.GceClusterConfig.MetadataValue))

    workflow_template = self.MakeWorkflowTemplate()
    self.ExpectCallSetManagedCluster(
        workflow_template=workflow_template, managed_cluster=managed_cluster)

    command = ('workflow-templates set-managed-cluster {template} '
               '--cluster-name {cluster_name} '
               '--bucket {bucket} '
               '--zone {zone} '
               '--num-mains {num_mains} '
               '--num-workers {num_workers} '
               '--main-machine-type {main_machine_type} '
               '--worker-machine-type {worker_machine_type} '
               '--network {network} '
               '--image-version {image_version} '
               '--initialization-action-timeout 2m '
               '--initialization-actions {actions} '
               '--num-secondary-workers {num_secondary} '
               '--service-account {service_account} '
               '--scopes {scopes} '
               '--properties core:com.foo=foo,hdfs:com.bar=bar '
               '--tags tag1,tag2 '
               '--metadata key1=value1,key2=value2 ').format(
                   template=self.WORKFLOW_TEMPLATE,
                   cluster_name=cluster_name,
                   bucket=bucket,
                   zone=zone,
                   num_mains=num_mains,
                   num_workers=num_workers,
                   main_machine_type=main_machine_type,
                   worker_machine_type=worker_machine_type,
                   network=network,
                   image_version=image_version,
                   actions=','.join(action_uris),
                   num_secondary=num_secondary_workers,
                   service_account=service_account,
                   scopes=scope_list)

    result = self.RunDataproc(command)
    self.AssertMessagesEqual(workflow_template, result)

  def testSetManagedClusterBetaFlags(self):
    cluster_name = 'test-cluster'
    main_accelerator_type = 'foo-gpu'
    worker_accelerator_type = 'bar-gpu'
    zone = 'foo-zone'
    image = 'test-image'
    image_uri = ('https://compute.googleapis.com/compute/beta/projects/'
                 'fake-project/global/images/test-image')
    main_machine_type = 'foo-type'
    worker_machine_type = 'bar-type'
    main_min_cpu_platform = 'Intel Skylake'
    worker_min_cpu_platform = 'Intel Haswell'
    managed_cluster = self.MakeManagedCluster(
        clusterName=cluster_name,
        projectId=self.Project(),
        mainAcceleratorTypeUri=main_accelerator_type,
        mainAcceleratorCount=1,
        workerAcceleratorTypeUri=worker_accelerator_type,
        workerAcceleratorCount=2,
        mainMachineTypeUri=main_machine_type,
        workerMachineTypeUri=worker_machine_type,
        mainBootDiskSizeGb=15,
        workerBootDiskSizeGb=30,
        secondaryWorkerBootDiskSizeGb=42,
        mainBootDiskType='pd-standard',
        workerBootDiskType='pd-ssd',
        secondaryWorkerBootDiskType='pd-standard',
        internalIpOnly=True,
        imageUri=image_uri,
        zoneUri=zone,
        enableHttpPortAccess=True)
    self.AddMinCpuPlatform(managed_cluster, main_min_cpu_platform,
                           worker_min_cpu_platform)

    workflow_template = self.MakeWorkflowTemplate()
    self.ExpectCallSetManagedCluster(
        workflow_template=workflow_template, managed_cluster=managed_cluster)

    command = ('workflow-templates set-managed-cluster {template} '
               '--cluster-name {cluster_name} '
               '--main-accelerator type={main_accelerator_type},count=1 '
               '--worker-accelerator type={worker_accelerator_type},count=2 '
               '--main-boot-disk-size 15GB '
               '--worker-boot-disk-size 30GB '
               '--main-boot-disk-type pd-standard '
               '--worker-boot-disk-type pd-ssd '
               '--main-machine-type {main_machine_type} '
               '--worker-machine-type {worker_machine_type} '
               '--image {image} '
               '--secondary-worker-boot-disk-size 42GB '
               '--secondary-worker-boot-disk-type pd-standard '
               '--main-min-cpu-platform="{main_min_cpu_platform}" '
               '--worker-min-cpu-platform="{worker_min_cpu_platform}" '
               '--no-address '
               '--zone {zone} '
               '--enable-component-gateway ').format(
                   template=self.WORKFLOW_TEMPLATE,
                   cluster_name=cluster_name,
                   main_accelerator_type=main_accelerator_type,
                   worker_accelerator_type=worker_accelerator_type,
                   main_machine_type=main_machine_type,
                   worker_machine_type=worker_machine_type,
                   main_min_cpu_platform=main_min_cpu_platform,
                   worker_min_cpu_platform=worker_min_cpu_platform,
                   image=image,
                   zone=zone)

    result = self.RunDataproc(command)
    self.AssertMessagesEqual(workflow_template, result)


class WorkflowTemplateSetManagedClusterUnitTestAlpha(
    WorkflowTemplateSetManagedClusterUnitTestBeta):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA
