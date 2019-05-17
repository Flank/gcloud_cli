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

"""Test of the 'clusters create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import copy
import os
import textwrap

from apitools.base.py import encoding
from googlecloudsdk import calliope

from googlecloudsdk.api_lib.dataproc import constants
from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import compute_base
from tests.lib.surface.dataproc import unit_base


class ClustersCreateUnitTest(
    unit_base.DataprocUnitTestBase, compute_base.BaseComputeUnitTest):
  """Tests for dataproc clusters create."""

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

  def ExpectCreateCallsWithWarnings(self):
    warnings = [
        'If you only have 640 KB of memory.',
        "You're gonna have a bad time.",
        "I don't think this is going to work.",
    ]
    self.ExpectCreateCluster()
    operation = self.MakeOperation(
        metadata=collections.OrderedDict([('warnings', warnings[:2])]))
    self.ExpectGetOperation(operation)
    self.ExpectGetOperation(operation)
    operation = self.MakeOperation(
        metadata=collections.OrderedDict([('warnings', warnings)]))
    self.ExpectGetOperation(operation)
    operation = self.MakeCompletedOperation(
        error=self.MakeRpcError(),
        metadata=collections.OrderedDict([('warnings', warnings)]))
    self.ExpectGetOperation(operation)

  def testCreateClusterDefaults(self):
    properties.VALUES.compute.zone.Set(self.ZONE)
    properties.VALUES.dataproc.region.Set('us-central1')
    request_cluster = self.MakeCluster()
    response_cluster = self.MakeRunningCluster()
    self.ExpectCreateCalls(
        request_cluster, response_cluster, region='us-central1')
    result = self.RunDataproc('clusters create {0}'.format(self.CLUSTER_NAME))
    self.AssertMessagesEqual(response_cluster, result)

  def testCreateClusterUri(self):
    properties.VALUES.compute.zone.Set(self.ZONE)
    request_cluster = self.MakeCluster()
    response_cluster = self.MakeRunningCluster()
    self.ExpectCreateCalls(request_cluster, response_cluster)
    result = self.RunDataproc('clusters create {0}'.format(self.ClusterUri()))
    self.AssertMessagesEqual(response_cluster, result)

  def testCreateClusterOmitZone(self):
    self.MockCompute()
    self.ExpectListZones()

    request_cluster = self.MakeCluster()
    response_cluster = self.MakeRunningCluster()
    self.ExpectCreateCalls(request_cluster, response_cluster)

    self.WriteInput('3\n')
    result = self.RunDataproc('clusters create {0}'.format(self.CLUSTER_NAME))
    self.AssertMessagesEqual(response_cluster, result)

    self.AssertErrContains('PROMPT_CHOICE')
    self.AssertErrContains(
        '"choices": ["europe-west1-a", "europe-west1-b (DELETED)", '
        '"us-central1-a (DEPRECATED)", "us-central1-b"]')
    self.AssertErrContains(
        textwrap.dedent("""\
        Waiting on operation [{operation}].
        {{"ux": "PROGRESS_TRACKER", "message": "Waiting for cluster creation operation", "status": "SUCCESS"}}
        Created [{cluster_uri}] Cluster placed in zone [{zone}].
        """.format(
            operation=self.OperationName(),
            cluster_uri=self.ClusterUri(),
            zone='us-central1-a')))

  def testCreateClusterOmitZone_provideRegion(self):
    self.MockCompute()

    request_cluster = self.MakeCluster()
    request_cluster.config.gceClusterConfig.zoneUri = ''
    response_cluster = self.MakeRunningCluster()
    # response zone uri is a full url to us-central1-a

    self.ExpectCreateCalls(
        request_cluster, response_cluster, region='us-central1')

    result = self.RunDataproc('clusters create --region={0} {1}'.format(
        'us-central1', self.CLUSTER_NAME))
    self.AssertMessagesEqual(response_cluster, result)

  def testCreateClusterFlags(self):
    project = 'foo-project'
    cluster_name = 'foo-cluster'
    zone = 'foo-zone'
    master_machine_type = 'foo-type'
    worker_machine_type = 'bar-type'
    bucket = 'foo-bucket'
    num_masters = 3
    num_workers = 7
    num_preemptible_workers = 5
    image_version = '1.7'
    network = 'foo-network'
    network_uri = ('https://www.googleapis.com/compute/v1/projects/'
                   'foo-project/global/networks/foo-network')
    action_uris = ['gs://my-bucket/action1.sh', 'gs://my-bucket/action2.sh']
    initialization_actions = [
        self.messages.NodeInitializationAction(
            executableFile=action_uris[0],
            executionTimeout='120s'),
        self.messages.NodeInitializationAction(
            executableFile=action_uris[1],
            executionTimeout='120s')]
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
    expected_request_cluster = self.MakeCluster(
        clusterName=cluster_name,
        configBucket=bucket,
        imageVersion=image_version,
        masterMachineTypeUri=master_machine_type,
        workerMachineTypeUri=worker_machine_type,
        networkUri=network_uri,
        masterConfigNumInstances=num_masters,
        workerConfigNumInstances=num_workers,
        secondaryWorkerConfigNumInstances=num_preemptible_workers,
        projectId=project,
        zoneUri=zone,
        initializationActions=initialization_actions,
        serviceAccount=service_account,
        serviceAccountScopes=scope_uris,
        internalIpOnly=True,
        properties=encoding.DictToAdditionalPropertyMessage(
            cluster_properties, self.messages.SoftwareConfig.PropertiesValue),
        tags=['tag1', 'tag2'],
        metadata=encoding.DictToAdditionalPropertyMessage(
            cluster_metadata, self.messages.GceClusterConfig.MetadataValue))

    self.AddEncryptionConfig(expected_request_cluster,
                             'projects/p/locations/l/keyRings/kr/cryptoKeys/k')
    self.AddComponents(expected_request_cluster, ['ANACONDA', 'ZEPPELIN'])
    expected_response_cluster = copy.deepcopy(expected_request_cluster)
    expected_response_cluster.status = self.messages.ClusterStatus(
        state=self.messages.ClusterStatus.StateValueValuesEnum.RUNNING)

    command = (
        'clusters --project {project} create {cluster} '
        '--bucket {bucket} '
        '--zone {zone} '
        '--num-masters {num_masters} '
        '--num-workers {num_workers} '
        '--master-machine-type {master_machine_type} '
        '--worker-machine-type {worker_machine_type} '
        '--network {network} '
        '--image-version {image_version} '
        '--initialization-action-timeout 2m '
        '--initialization-actions {actions} '
        '--num-preemptible-workers {num_preemptible} '
        '--service-account {service_account} '
        '--scopes {scopes} '
        '--no-address '
        '--properties core:com.foo=foo,hdfs:com.bar=bar '
        '--tags tag1,tag2 '
        '--metadata key1=value1,key2=value2 '
        '--optional-components=anaconda,zeppelin '
        '--gce-pd-kms-key-project=p '
        '--gce-pd-kms-key-location=l '
        '--gce-pd-kms-key-keyring=kr '
        '--gce-pd-kms-key=k '
    ).format(
        project=project,
        cluster=cluster_name,
        bucket=bucket,
        zone=zone,
        num_masters=num_masters,
        num_workers=num_workers,
        master_machine_type=master_machine_type,
        worker_machine_type=worker_machine_type,
        network=network,
        image_version=image_version,
        actions=','.join(action_uris),
        num_preemptible=num_preemptible_workers,
        service_account=service_account,
        scopes=scope_list)

    self.ExpectCreateCalls(
        request_cluster=expected_request_cluster,
        response_cluster=expected_response_cluster)
    result = self.RunDataproc(command)
    self.AssertMessagesEqual(expected_response_cluster, result)

  def testCreateHiddenFlags(self):
    """Tests flags that cover flags hidden in all tracks."""
    request_cluster = self.MakeCluster()
    response_cluster = self.MakeRunningCluster()
    self.ExpectCreateCalls(request_cluster, response_cluster)
    result = self.RunDataproc((
        'clusters create {cluster} '
        '--timeout {timeout} '
        '--zone {zone} '
    ).format(
        cluster=self.CLUSTER_NAME,
        timeout='42s',
        zone=self.ZONE))
    self.AssertMessagesEqual(response_cluster, result)

  def testCreateClustersSubnetwork(self):
    properties.VALUES.compute.zone.Set(self.ZONE)
    request_cluster = self.MakeCluster(
        networkUri=None, subnetworkUri=self.SubnetUri())
    response_cluster = self.MakeRunningCluster(
        networkUri=None, subnetworkUri=self.SubnetUri())
    self.ExpectCreateCalls(request_cluster, response_cluster)
    result = self.RunDataproc(
        'clusters create {0} --subnet {1}'.format(
            self.CLUSTER_NAME, self.SUBNET))
    self.AssertMessagesEqual(response_cluster, result)

  def testCreateClustersLabels(self):
    labels = {'k1': 'v1'}
    properties.VALUES.compute.zone.Set(self.ZONE)
    request_cluster = self.MakeCluster(
        networkUri=None, subnetworkUri=self.SubnetUri(), labels=labels)
    response_cluster = self.MakeRunningCluster(
        networkUri=None, subnetworkUri=self.SubnetUri(), labels=labels)
    self.assertTrue(request_cluster.labels is not None)
    self.assertTrue(response_cluster.labels is not None)
    self.ExpectCreateCalls(request_cluster=request_cluster,
                           response_cluster=response_cluster)
    result = self.RunDataproc(
        command='clusters create {0} --labels=k1=v1 --subnet {1}'.format(
            self.CLUSTER_NAME, self.SUBNET))
    self.assertTrue(result.labels is not None)
    self.assertEqual(response_cluster.labels, result.labels)
    self.AssertMessagesEqual(response_cluster, result)

  def testCreateClusterOperationFailure(self):
    properties.VALUES.compute.zone.Set(self.ZONE)
    self.ExpectCreateCalls(error=self.MakeRpcError())
    with self.AssertRaisesExceptionMatches(
        exceptions.OperationError,
        'Operation [{0}] failed: There was an error with the operation!'.format(
            self.OperationName())):
      self.RunDataproc('clusters create {0}'.format(self.CLUSTER_NAME))

  def testCreateClustersPermissionsError(self):
    properties.VALUES.compute.zone.Set(self.ZONE)
    self.ExpectCreateCluster(
        exception=self.MakeHttpError(403))
    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc('clusters create {0}'.format(self.CLUSTER_NAME))

  def testCreateClustersNetworkAndSubnetwork(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --network: At most one of '
        '--network | --subnet may be specified.'):
      self.RunDataproc(
          'clusters create {0} --network foo --subnet bar'.format(
              self.CLUSTER_NAME))

  def testCreateClustersAsync(self):
    properties.VALUES.compute.zone.Set(self.ZONE)
    self.ExpectCreateCluster()
    self.RunDataproc('clusters create {0} --async'.format(self.CLUSTER_NAME))
    self.AssertErrContains('Creating [{0}] with operation [{1}].'.format(
        self.ClusterUri(), self.OperationName()))

  def testCreateClusterUnsupportedNumMasters(self):
    masters = 2
    err_message = ('Number of masters must be 1 (Standard) or 3 '
                   '(High Availability)')
    with self.AssertRaisesArgumentErrorMatches(err_message):
      self.RunDataproc(
          'clusters create {name} --zone={zone} --num-masters={masters}'.format(
              name=self.CLUSTER_NAME, zone=self.ZONE, masters=masters))

  def testCreateClusterWarnings(self):
    properties.VALUES.compute.zone.Set(self.ZONE)
    self.ExpectCreateCallsWithWarnings()
    with self.AssertRaisesExceptionMatches(
        exceptions.OperationError,
        'Operation [{0}] failed: There was an error with the operation!'.format(
            self.OperationName())):
      self.RunDataproc('clusters create {0}'.format(self.CLUSTER_NAME))
    self.AssertErrContains(
        """\
        WARNING: If you only have 640 KB of memory.
        WARNING: You're gonna have a bad time.
        WARNING: I don't think this is going to work.""",
        normalize_space=True)
    # Ensure warnings only appear once.
    self.AssertErrNotMatches(r'.*(WARNING(.|\n)*){4}')

  def testCreateClusterWarningsInteractive(self):
    self.StartObjectPatch(console_io, 'IsInteractive').return_value = True
    properties.VALUES.compute.zone.Set(self.ZONE)
    self.ExpectCreateCallsWithWarnings()
    with self.AssertRaisesExceptionMatches(
        exceptions.OperationError,
        'Operation [{0}] failed: There was an error with the operation!'.format(
            self.OperationName())):
      self.RunDataproc('clusters create {0}'.format(self.CLUSTER_NAME))
    # Ensure newlines are printed correctly.
    self.AssertErrContains('Waiting for cluster creation operation')
    self.AssertErrContains("""\
        WARNING: If you only have 640 KB of memory.
        WARNING: You're gonna have a bad time.""", normalize_space=True)
    self.AssertErrContains("WARNING: I don't think this is going to work.")
    # Ensure warnings only appear once.
    self.AssertErrNotMatches(r'.*(WARNING(.|\n)*){4}')

  def testCreateSingleNode(self):
    dataproc_properties = encoding.DictToAdditionalPropertyMessage({
        constants.ALLOW_ZERO_WORKERS_PROPERTY: 'true'
    }, self.messages.SoftwareConfig.PropertiesValue)
    expected_request_cluster = self.MakeCluster(properties=dataproc_properties)
    expected_response_cluster = self.MakeRunningCluster(
        properties=dataproc_properties)
    self.ExpectCreateCalls(
        request_cluster=expected_request_cluster,
        response_cluster=expected_response_cluster)
    result = self.RunDataproc(
        'clusters create {name} --zone={zone} --single-node'.format(
            name=self.CLUSTER_NAME, zone=self.ZONE))
    self.AssertMessagesEqual(expected_response_cluster, result)

  def testCreateSingleNodeUsingNumWorkersFlag(self):
    dataproc_properties = encoding.DictToAdditionalPropertyMessage({
        constants.ALLOW_ZERO_WORKERS_PROPERTY: 'true'
    }, self.messages.SoftwareConfig.PropertiesValue)
    expected_request_cluster = self.MakeCluster(
        properties=dataproc_properties, workerConfigNumInstances=0)
    expected_response_cluster = self.MakeRunningCluster(
        properties=dataproc_properties)
    self.ExpectCreateCalls(
        request_cluster=expected_request_cluster,
        response_cluster=expected_response_cluster)
    result = self.RunDataproc(
        'clusters create {name} --zone={zone} --num-workers=0'.format(
            name=self.CLUSTER_NAME, zone=self.ZONE))
    self.AssertMessagesEqual(expected_response_cluster, result)

  def testCreateSingleNodeWithSingleNodeAndNumWorkersFlagZero(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --single-node: At most one of --single-node | '
        '--num-preemptible-workers --num-workers may be specified.'):
      self.RunDataproc(
          'clusters create {name} --zone={zone} --single-node --num-workers=0'.
          format(name=self.CLUSTER_NAME, zone=self.ZONE))

  def testCreateSingleNodeWithWorkers(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --single-node: At most one of --single-node | '
        '--num-preemptible-workers --num-workers may be specified.'):
      self.RunDataproc('clusters create {name} --zone={zone} '
                       '--num-workers=2 --single-node'.format(
                           name=self.CLUSTER_NAME, zone=self.ZONE))

  def testCreateSingleNodeWithPreemtibleWorkers(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --single-node: At most one of --single-node | '
        '--num-preemptible-workers --num-workers may be specified.'):
      self.RunDataproc('clusters create {name} --zone={zone} '
                       '--num-preemptible-workers=2 --single-node'.format(
                           name=self.CLUSTER_NAME, zone=self.ZONE))

  def testCreateSpecifyUnsupportedSingleNodeProperty(self):
    with self.AssertRaisesExceptionMatches(
        calliope.exceptions.InvalidArgumentException,
        'Instead of %s, use gcloud beta dataproc clusters create '
        '--single-node to deploy single node clusters' %
        constants.ALLOW_ZERO_WORKERS_PROPERTY):
      self.RunDataproc(
          'clusters create {name} --zone={zone} '
          '--properties={allow_zero_workers_prop}=true'.format(
              name=self.CLUSTER_NAME,
              zone=self.ZONE,
              allow_zero_workers_prop=constants.ALLOW_ZERO_WORKERS_PROPERTY))

  def testCreateWithUrls(self):
    """Tests zonal resource urls."""
    project = 'foo-project'
    cluster_name = 'foo-cluster'
    zone_url = ('https://www.googleapis.com/compute/v1/projects/'
                'foo-project/zones/foo-zone')
    master_machine_type_url = (
        'https://www.googleapis.com/compute/v1/projects/'
        'foo-project/zones/foo-zone/machineTypes/foo-type')
    worker_machine_type_url = (
        'https://www.googleapis.com/compute/v1/projects/'
        'foo-project/zones/foo-zone/machineTypes/bar-type')
    expected_request_cluster = self.MakeCluster(
        clusterName=cluster_name,
        projectId=project,
        masterMachineTypeUri=master_machine_type_url,
        workerMachineTypeUri=worker_machine_type_url,
        zoneUri=zone_url)

    expected_response_cluster = copy.deepcopy(expected_request_cluster)
    expected_response_cluster.status = self.messages.ClusterStatus(
        state=self.messages.ClusterStatus.StateValueValuesEnum.RUNNING)

    command = ('clusters --project {project} create {cluster} '
               '--master-machine-type {master_machine_type} '
               '--worker-machine-type {worker_machine_type} '
               '--zone {zone} ').format(
                   project=project,
                   cluster=cluster_name,
                   master_machine_type=master_machine_type_url,
                   worker_machine_type=worker_machine_type_url,
                   zone=zone_url)

    self.ExpectCreateCalls(
        request_cluster=expected_request_cluster,
        response_cluster=expected_response_cluster)
    result = self.RunDataproc(command)
    self.AssertMessagesEqual(expected_response_cluster, result)

  def testCreateClusterNoOperationGetPermission(self):
    properties.VALUES.compute.zone.Set(self.ZONE)
    operation = self.MakeOperation()
    self.ExpectCreateCluster(response=operation)
    self.ExpectGetOperation(
        operation=operation, exception=self.MakeHttpError(403))
    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc('clusters create {0}'.format(self.CLUSTER_NAME))

  def testCreateClusterWithImagesFlags(self):
    project = 'fake-project'
    cluster_name = 'foo-cluster'
    zone = 'foo-zone'
    image = 'test-image'
    image_uri = self.ImageUri()
    expected_request_cluster = self.MakeCluster(
        clusterName=cluster_name,
        imageUri=image_uri,
        projectId=project,
        zoneUri=zone)

    expected_response_cluster = copy.deepcopy(expected_request_cluster)
    expected_response_cluster.status = self.messages.ClusterStatus(
        state=self.messages.ClusterStatus.StateValueValuesEnum.RUNNING)

    command = ('clusters --project {project} create {cluster} '
               '--zone {zone} '
               '--image {image} ').format(
                   project=project,
                   cluster=cluster_name,
                   zone=zone,
                   image=image)

    self.ExpectCreateCalls(
        request_cluster=expected_request_cluster,
        response_cluster=expected_response_cluster)
    result = self.RunDataproc(command)
    self.AssertMessagesEqual(expected_response_cluster, result)

  def testCreateClusterWithImageVersionFlags(self):
    project = 'foo-project'
    cluster_name = 'foo-cluster'
    zone = 'foo-zone'
    image_version = '1.7'
    expected_request_cluster = self.MakeCluster(
        clusterName=cluster_name,
        imageVersion=image_version,
        projectId=project,
        zoneUri=zone)

    expected_response_cluster = copy.deepcopy(expected_request_cluster)
    expected_response_cluster.status = self.messages.ClusterStatus(
        state=self.messages.ClusterStatus.StateValueValuesEnum.RUNNING)

    command = ('clusters --project {project} create {cluster} '
               '--zone {zone} '
               '--image-version {imageVersion} ').format(
                   project=project,
                   cluster=cluster_name,
                   zone=zone,
                   imageVersion=image_version)

    self.ExpectCreateCalls(
        request_cluster=expected_request_cluster,
        response_cluster=expected_response_cluster)
    result = self.RunDataproc(command)
    self.AssertMessagesEqual(expected_response_cluster, result)

  def testCreateClusterWithImagesFlags_mutualExclusion(self):
    project = 'foo-project'
    cluster_name = 'foo-cluster'
    zone = 'foo-zone'
    image_version = '1.7'
    image = 'test-image'

    command = ('clusters --project {project} create {cluster} '
               '--zone {zone} '
               '--image {image} '
               '--image-version {imageVersion} ').format(
                   project=project,
                   cluster=cluster_name,
                   zone=zone,
                   image=image,
                   imageVersion=image_version)

    with self.AssertRaisesArgumentErrorMatches(
        'argument --image: At most one of --image | '
        '--image-version may be specified.'):
      self.RunDataproc(command)

  def testCreateClusterWithIncompleteGcePdKmsKeyFlags_NoLocation(self):
    """Test command partially specified gce-pd-kms-key flags fail."""
    # No Location
    with self.AssertRaisesExceptionMatches(
        exceptions.ArgumentError, '--gce-pd-kms-key was not fully specified.'):
      self.RunDataproc(
          ('clusters create {cluster} --zone={zone} '
           '--gce-pd-kms-key-project={keyProject} '
           '--gce-pd-kms-key-keyring={keyRing} '
           '--gce-pd-kms-key={key}').format(
               cluster='test-cluster',
               zone='test-zone',
               keyProject='test-project',
               keyRing='test-keyring',
               key='test-key'))

  def testCreateClusterWithIncompleteGcePdKmsKeyFlags_NoKeyring(self):
    """Test command partially specified gce-pd-kms-key flags fail."""
    # No KeyRing
    with self.AssertRaisesExceptionMatches(
        exceptions.ArgumentError, '--gce-pd-kms-key was not fully specified.'):
      self.RunDataproc(
          ('clusters create {cluster} --zone={zone} '
           '--gce-pd-kms-key-project={keyProject} '
           '--gce-pd-kms-key-location={keyLocation} '
           '--gce-pd-kms-key={key}').format(
               cluster='test-cluster',
               zone='test-zone',
               keyProject='test-project',
               keyLocation='test-key-location',
               key='test-key'))

  def testCreateClusterWithIncompleteGcePdKmsKeyFlags_NoKey(self):
    """Test command partially specified gce-pd-kms-key flags fail."""
    # No Key
    with self.AssertRaisesArgumentErrorMatches(
        'argument --gce-pd-kms-key-keyring --gce-pd-kms-key-location '
        '--gce-pd-kms-key-project: --gce-pd-kms-key must be specified.'):
      self.RunDataproc(
          ('clusters create {cluster} --zone={zone} '
           '--gce-pd-kms-key-project={keyProject} '
           '--gce-pd-kms-key-location={keyLocation} '
           '--gce-pd-kms-key-keyring={keyRing}').format(
               cluster='test-cluster',
               zone='test-zone',
               keyProject='test-project',
               keyLocation='test-key-location',
               keyRing='test-keyring'))

  def testCreateClusterWithInvalidRelativeName(self):
    """Test command partially specified gce-pd-kms-key flags fail."""
    # Invalid relative name
    with self.AssertRaisesExceptionMatches(
        exceptions.ArgumentError, '--gce-pd-kms-key was not fully specified.'):
      self.RunDataproc(
          ('clusters create {cluster} --zone={zone} '
           '--gce-pd-kms-key={key}').format(
               cluster='test-cluster',
               zone='test-zone',
               key='locations/l/keyRings/kr/cryptoKeys/k'))


class ClustersCreateUnitTestBeta(ClustersCreateUnitTest,
                                 base.DataprocTestBaseBeta):

  def testTrack(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope.base.ReleaseTrack.BETA)

  def testCreateClusterFlags(self):
    """Tests flags that behave differently in Beta track."""
    project = 'foo-project'
    master_accelerator_type = 'foo-gpu'
    worker_accelerator_type = 'bar-gpu'
    cluster_name = 'foo-cluster'
    zone = 'foo-zone'
    master_machine_type = 'foo-type'
    worker_machine_type = 'bar-type'
    master_min_cpu_platform = 'Intel Skylake'
    worker_min_cpu_platform = 'Intel Haswell'
    expected_request_cluster = self.MakeCluster(
        clusterName=cluster_name,
        projectId=project,
        masterAcceleratorTypeUri=master_accelerator_type,
        masterAcceleratorCount=1,
        workerAcceleratorTypeUri=worker_accelerator_type,
        workerAcceleratorCount=2,
        masterMachineTypeUri=master_machine_type,
        workerMachineTypeUri=worker_machine_type,
        masterBootDiskSizeGb=15,
        workerBootDiskSizeGb=30,
        secondaryWorkerBootDiskSizeGb=42,
        masterBootDiskType='pd-standard',
        workerBootDiskType='pd-ssd',
        secondaryWorkerBootDiskType='pd-standard',
        internalIpOnly=True,
        zoneUri=zone,
        enableHttpPortAccess=True)
    autoscaling_policy_uri = ('projects/foo-project/regions/foo-region/'
                              'autoscalingPolicies/foo-policy')
    self.AddAutoscalingConfig(expected_request_cluster, autoscaling_policy_uri)
    self.AddMinCpuPlatform(expected_request_cluster, master_min_cpu_platform,
                           worker_min_cpu_platform)
    self.AddEncryptionConfig(expected_request_cluster,
                             'projects/p/locations/l/keyRings/kr/cryptoKeys/k')
    self.AddComponents(expected_request_cluster, ['ANACONDA', 'ZEPPELIN'])
    expected_response_cluster = copy.deepcopy(expected_request_cluster)
    expected_response_cluster.status = self.messages.ClusterStatus(
        state=self.messages.ClusterStatus.StateValueValuesEnum.RUNNING)
    self.AddMinCpuPlatform(expected_response_cluster, master_min_cpu_platform,
                           worker_min_cpu_platform)

    command = ('clusters --project {project} create {cluster} '
               '--master-accelerator type={master_accelerator_type},count=1 '
               '--worker-accelerator type={worker_accelerator_type},count=2 '
               '--master-boot-disk-size 15GB '
               '--worker-boot-disk-size 30GB '
               '--master-boot-disk-type pd-standard '
               '--worker-boot-disk-type pd-ssd '
               '--master-machine-type {master_machine_type} '
               '--worker-machine-type {worker_machine_type} '
               '--preemptible-worker-boot-disk-size 42GB '
               '--preemptible-worker-boot-disk-type pd-standard '
               '--no-address '
               '--master-min-cpu-platform="{master_min_cpu_platform}" '
               '--worker-min-cpu-platform="{worker_min_cpu_platform}" '
               '--gce-pd-kms-key-project=p '
               '--gce-pd-kms-key-location=l '
               '--gce-pd-kms-key-keyring=kr '
               '--gce-pd-kms-key=k '
               '--optional-components=anaconda,zeppelin '
               '--zone {zone} '
               '--autoscaling-policy {autoscaling_policy_uri} '
               '--enable-component-gateway ').format(
                   project=project,
                   cluster=cluster_name,
                   master_accelerator_type=master_accelerator_type,
                   worker_accelerator_type=worker_accelerator_type,
                   master_machine_type=master_machine_type,
                   worker_machine_type=worker_machine_type,
                   master_min_cpu_platform=master_min_cpu_platform,
                   worker_min_cpu_platform=worker_min_cpu_platform,
                   zone=zone,
                   autoscaling_policy_uri=autoscaling_policy_uri)

    self.ExpectCreateCalls(
        request_cluster=expected_request_cluster,
        response_cluster=expected_response_cluster)
    result = self.RunDataproc(command)
    self.AssertMessagesEqual(expected_response_cluster, result)

  def testCreateWithUrls(self):
    """Tests zonal resource urls specific to Beta track."""
    project = 'foo-project'
    master_accelerator_type_url = (
        'https://www.googleapis.com/compute/beta/projects/'
        'foo-project/zones/foo-zone/acceleratorTypes/foo-gpu')
    worker_accelerator_type_url = (
        'https://www.googleapis.com/compute/beta/projects/'
        'foo-project/zones/foo-zone/acceleratorTypes/bar-gpu')
    cluster_name = 'foo-cluster'
    zone = 'foo-zone'

    expected_request_cluster = self.MakeCluster(
        clusterName=cluster_name,
        projectId=project,
        masterAcceleratorTypeUri=master_accelerator_type_url,
        masterAcceleratorCount=1,
        workerAcceleratorTypeUri=worker_accelerator_type_url,
        workerAcceleratorCount=2,
        zoneUri=zone)
    command = ('clusters --project {project} create {cluster} '
               '--master-accelerator type={master_accelerator_type},count=1 '
               '--worker-accelerator type={worker_accelerator_type},count=2 '
               '--zone {zone} ').format(
                   project=project,
                   cluster=cluster_name,
                   master_accelerator_type=master_accelerator_type_url,
                   worker_accelerator_type=worker_accelerator_type_url,
                   zone=zone)

    expected_response_cluster = copy.deepcopy(expected_request_cluster)
    expected_response_cluster.status = self.messages.ClusterStatus(
        state=self.messages.ClusterStatus.StateValueValuesEnum.RUNNING)

    self.ExpectCreateCalls(
        request_cluster=expected_request_cluster,
        response_cluster=expected_response_cluster)
    result = self.RunDataproc(command)
    self.AssertMessagesEqual(expected_response_cluster, result)

  def testCreateClusterWithExpirationTimeAndMaxIdle(self):
    """Tests TTL cluster related flags."""
    project = 'foo-project'
    cluster_name = 'foo-ttl-cluster'
    zone = 'foo-zone'

    expected_request_cluster = self.MakeCluster(
        clusterName=cluster_name, projectId=project, zoneUri=zone)
    expected_request_cluster.config.lifecycleConfig = (
        self.messages.LifecycleConfig(
            idleDeleteTtl='1800s',
            autoDeleteTime='2017-08-25T00:00:00.000-07:00'))
    expected_response_cluster = copy.deepcopy(expected_request_cluster)
    expected_response_cluster.status = self.messages.ClusterStatus(
        state=self.messages.ClusterStatus.StateValueValuesEnum.RUNNING)

    self.ExpectCreateCalls(
        request_cluster=expected_request_cluster,
        response_cluster=expected_response_cluster)

    command = ('clusters --project {project} create {cluster} '
               '--zone {zone} '
               '--max-idle={max_idle} '
               '--expiration-time={expiration_time} ').format(
                   project=project,
                   cluster=cluster_name,
                   zone=zone,
                   max_idle='30m',
                   expiration_time='2017-08-25T00:00:00-07:00')
    result = self.RunDataproc(command)
    self.AssertMessagesEqual(expected_response_cluster, result)

  def testCreateClusterWithExpirationTimeAndMaxAge(self):
    """Tests run command with mutual-exclusive TTL cluster flags."""
    with self.AssertRaisesArgumentErrorMatches(
        'argument --expiration-time: At most one of --expiration-time | '
        '--max-age may be specified.'):
      self.RunDataproc((
          'clusters create {cluster} --max-idle={max_idle} '
          '--max-age={max_age} '
          '--expiration-time={expiration_time} ').format(
              cluster=self.CLUSTER_NAME,
              max_idle='30m',
              max_age='1h',
              expiration_time='2017-08-25T00:00:00-07:00'))

  def testCreateClusterWithMinCpuPlatformPreemtibleWorkers(self):
    expected_request_cluster = self.MakeCluster(
        secondaryWorkerConfigNumInstances=2)
    self.AddMinCpuPlatform(expected_request_cluster, None, 'Intel Haswell')
    expected_response_cluster = self.MakeRunningCluster()
    self.AddMinCpuPlatform(expected_response_cluster, None, 'Intel Haswell')
    self.ExpectCreateCalls(
        request_cluster=expected_request_cluster,
        response_cluster=expected_response_cluster)
    result = self.RunDataproc(
        'clusters create {name} --zone={zone} --num-preemptible-workers=2 '
        '--worker-min-cpu-platform="Intel Haswell"'.format(
            name=self.CLUSTER_NAME, zone=self.ZONE))
    self.AssertMessagesEqual(expected_response_cluster, result)

  def testCreateClusterWithMinCpuPlatformAndWithoutPreemtibleWorkers(self):
    expected_request_cluster = self.MakeCluster()
    self.AddMinCpuPlatform(expected_request_cluster, None, 'Intel Haswell')
    expected_response_cluster = self.MakeRunningCluster()
    self.AddMinCpuPlatform(expected_response_cluster, None, 'Intel Haswell')
    self.ExpectCreateCalls(
        request_cluster=expected_request_cluster,
        response_cluster=expected_response_cluster)
    result = self.RunDataproc(
        'clusters create {name} --zone={zone} '
        '--worker-min-cpu-platform="Intel Haswell"'.format(
            name=self.CLUSTER_NAME, zone=self.ZONE))
    self.AssertMessagesEqual(expected_response_cluster, result)

  def testCreateClusterReservationAffinity(self):
    project = 'foo-project'
    cluster_name = 'foo-cluster'
    zone = 'foo-zone'
    reservation_affinity = 'specific'
    reservation_label = 'key=name,value=test'
    reservation_label_key = 'name'
    reservation_label_value = 'test'
    expected_request_cluster = self.MakeCluster(
        clusterName=cluster_name, projectId=project, zoneUri=zone)
    self.AddReservationAffinity(expected_request_cluster, reservation_affinity,
                                reservation_label_key, reservation_label_value)

    expected_response_cluster = copy.deepcopy(expected_request_cluster)
    expected_response_cluster.status = self.messages.ClusterStatus(
        state=self.messages.ClusterStatus.StateValueValuesEnum.RUNNING)

    command = ('clusters --project {project} create {cluster} '
               '--zone {zone} '
               '--reservation-affinity {reservation_affinity} '
               '--reservation-label {reservation_label} ').format(
                   project=project,
                   cluster=cluster_name,
                   zone=zone,
                   reservation_affinity=reservation_affinity,
                   reservation_label=reservation_label)

    self.ExpectCreateCalls(
        request_cluster=expected_request_cluster,
        response_cluster=expected_response_cluster)
    result = self.RunDataproc(command)
    self.AssertMessagesEqual(expected_response_cluster, result)

  def testCreateKerberosFlagsMissingKmsKey(self):
    password_uri = 'gs://my-bucket/password.encrypted'
    error_msg = ('argument (--kerberos-kms-key : '
                 '--kerberos-kms-key-keyring '
                 '--kerberos-kms-key-location '
                 '--kerberos-kms-key-project): '
                 'Must be specified.')
    with self.AssertRaisesArgumentErrorMatches(error_msg):
      self.RunDataproc(
          ('clusters create {name} '
           '--zone={zone} '
           '--kerberos-root-principal-password-uri={password_uri}').format(
               name=self.CLUSTER_NAME,
               zone=self.ZONE,
               password_uri=password_uri))

  def testCreateKerberosFlagsMissingRootPrincipalPasswordUri(self):
    kms_project = 'my-project'
    kms_location = 'global'
    kms_keyring = 'my-keyring'
    kms_key = 'my-key'
    error_msg = ('argument --kerberos-root-principal-password-uri: '
                 'Must be specified.')
    with self.AssertRaisesArgumentErrorMatches(error_msg):
      self.RunDataproc(('clusters create {name} '
                        '--zone={zone} '
                        '--kerberos-kms-key={kms_key} '
                        '--kerberos-kms-key-project={kms_project} '
                        '--kerberos-kms-key-location={kms_location} '
                        '--kerberos-kms-key-keyring={kms_keyring}').format(
                            name=self.CLUSTER_NAME,
                            zone=self.ZONE,
                            kms_key=kms_key,
                            kms_project=kms_project,
                            kms_location=kms_location,
                            kms_keyring=kms_keyring))

  def testCreateKerberosFlagsKmsKeyOneFlag(self):
    password_uri = 'gs://my-bucket/password.encrypted'
    kms_key_uri = ('projects/my-project/locations/global/'
                   'keyRings/my-keyring/cryptoKeys/my-key')
    expected_request_cluster = self.MakeCluster()
    self.AddKerberosConfig(
        expected_request_cluster,
        enableKerberos=True,
        kerberosRootPrincipalPasswordUri=password_uri,
        kerberosKmsKeyUri=kms_key_uri)
    expected_response_cluster = self.MakeRunningCluster()
    self.AddKerberosConfig(
        expected_response_cluster,
        enableKerberos=True,
        kerberosRootPrincipalPasswordUri=password_uri,
        kerberosKmsKeyUri=kms_key_uri)
    self.ExpectCreateCalls(
        request_cluster=expected_request_cluster,
        response_cluster=expected_response_cluster)
    result = self.RunDataproc(
        ('clusters create {name} '
         '--zone={zone} '
         '--kerberos-root-principal-password-uri={password_uri} '
         '--kerberos-kms-key={kms_key_uri} ').format(
             name=self.CLUSTER_NAME,
             zone=self.ZONE,
             password_uri=password_uri,
             kms_key_uri=kms_key_uri))
    self.AssertMessagesEqual(expected_response_cluster, result)

  def testCreateKerberosFlags(self):
    password_uri = 'gs://my-bucket/password.encrypted'
    kms_project = 'my-project'
    kms_location = 'global'
    kms_keyring = 'my-keyring'
    kms_key = 'my-key'
    kms_key_uri = ('projects/{kms_project}/locations/{kms_location}/'
                   'keyRings/{kms_keyring}/cryptoKeys/{kms_key}').format(
                       kms_project=kms_project,
                       kms_location=kms_location,
                       kms_keyring=kms_keyring,
                       kms_key=kms_key)
    expected_request_cluster = self.MakeCluster()
    self.AddKerberosConfig(
        expected_request_cluster,
        enableKerberos=True,
        kerberosRootPrincipalPasswordUri=password_uri,
        kerberosKmsKeyUri=kms_key_uri)
    expected_response_cluster = self.MakeRunningCluster()
    self.AddKerberosConfig(
        expected_response_cluster,
        enableKerberos=True,
        kerberosRootPrincipalPasswordUri=password_uri,
        kerberosKmsKeyUri=kms_key_uri)
    self.ExpectCreateCalls(
        request_cluster=expected_request_cluster,
        response_cluster=expected_response_cluster)
    result = self.RunDataproc(
        ('clusters create {name} '
         '--zone={zone} '
         '--kerberos-root-principal-password-uri={password_uri} '
         '--kerberos-kms-key={kms_key} '
         '--kerberos-kms-key-project={kms_project} '
         '--kerberos-kms-key-location={kms_location} '
         '--kerberos-kms-key-keyring={kms_keyring}').format(
             name=self.CLUSTER_NAME,
             zone=self.ZONE,
             password_uri=password_uri,
             kms_key=kms_key,
             kms_project=kms_project,
             kms_location=kms_location,
             kms_keyring=kms_keyring))
    self.AssertMessagesEqual(expected_response_cluster, result)

  def testCreateKerberosFromFile(self):
    root_principal_password_uri = 'gs://my-bucket/password.encrypted'
    kms_key_uri = ('projects/my-project/locations/global/'
                   'keyRings/my-key-ring/cryptoKeys/my-key')
    kdc_db_key_uri = 'gs://my-bucket/kdc_db_key.encrypted'
    tgt_lifetime_hours = 10
    keystore_uri = 'gs://my-bucket/keystore.jks'
    keystore_password_uri = 'gs://my-bucket/keystore_password.encrypted'
    key_password_uri = 'gs://my-bucket/key_password.encrypted'
    truststore_uri = 'gs://my-bucket/truststore.jks'
    truststore_password_uri = 'gs://my-bucket/truststore_password.encrypted'
    cross_realm_trust_realm = 'REMOTE.REALM'
    cross_realm_trust_kdc = 'kdc.remote.realm'
    cross_realm_trust_admin_server = 'admin-server.remote.realm'
    cross_realm_trust_shared_password_uri = \
      'gs://my-bucket/shared_password.encrypted'
    kerberos_config_data = dict(
        root_principal_password_uri=root_principal_password_uri,
        kms_key_uri=kms_key_uri,
        kdc_db_key_uri=kdc_db_key_uri,
        tgt_lifetime_hours=tgt_lifetime_hours,
        ssl=dict(
            keystore_uri=keystore_uri,
            keystore_password_uri=keystore_password_uri,
            key_password_uri=key_password_uri,
            truststore_uri=truststore_uri,
            truststore_password_uri=truststore_password_uri),
        cross_realm_trust=dict(
            realm=cross_realm_trust_realm,
            kdc=cross_realm_trust_kdc,
            admin_server=cross_realm_trust_admin_server,
            shared_password_uri=cross_realm_trust_shared_password_uri))
    file_name = os.path.join(self.temp_path, 'kerberos_config_file_all.yaml')
    with files.FileWriter(file_name) as out_stream:
      yaml.dump(kerberos_config_data, stream=out_stream)

    expected_request_cluster = self.MakeCluster()
    self.AddKerberosConfig(
        expected_request_cluster,
        enableKerberos=True,
        kerberosRootPrincipalPasswordUri=root_principal_password_uri,
        kerberosKmsKeyUri=kms_key_uri,
        kerberosKdcDbKeyUri=kdc_db_key_uri,
        kerberosTgtLifetimeHours=tgt_lifetime_hours,
        kerberosKeystoreUri=keystore_uri,
        kerberosKeystorePasswordUri=keystore_password_uri,
        kerberosKeyPasswordUri=key_password_uri,
        kerberosTruststoreUri=truststore_uri,
        kerberosTruststorePasswordUri=truststore_password_uri,
        kerberosCrossRealmTrustRealm=cross_realm_trust_realm,
        kerberosCrossRealmTrustKdc=cross_realm_trust_kdc,
        kerberosCrossRealmTrustAdminServer=cross_realm_trust_admin_server,
        kerberosCrossRealmTrustSharedPasswordUri=cross_realm_trust_shared_password_uri
    )

    expected_response_cluster = self.MakeRunningCluster()
    self.AddKerberosConfig(
        expected_response_cluster,
        enableKerberos=True,
        kerberosRootPrincipalPasswordUri=root_principal_password_uri,
        kerberosKmsKeyUri=kms_key_uri,
        kerberosKdcDbKeyUri=kdc_db_key_uri,
        kerberosTgtLifetimeHours=tgt_lifetime_hours,
        kerberosKeystoreUri=keystore_uri,
        kerberosKeystorePasswordUri=keystore_password_uri,
        kerberosKeyPasswordUri=key_password_uri,
        kerberosTruststoreUri=truststore_uri,
        kerberosTruststorePasswordUri=truststore_password_uri,
        kerberosCrossRealmTrustRealm=cross_realm_trust_realm,
        kerberosCrossRealmTrustKdc=cross_realm_trust_kdc,
        kerberosCrossRealmTrustAdminServer=cross_realm_trust_admin_server,
        kerberosCrossRealmTrustSharedPasswordUri=cross_realm_trust_shared_password_uri
    )

    self.ExpectCreateCalls(
        request_cluster=expected_request_cluster,
        response_cluster=expected_response_cluster)
    result = self.RunDataproc(
        ('clusters create {name} '
         '--zone={zone} '
         '--kerberos-config-file={kerberos_config_file}').format(
             name=self.CLUSTER_NAME,
             zone=self.ZONE,
             kerberos_config_file=file_name))
    self.AssertMessagesEqual(expected_response_cluster, result)

  def testCreateCluster_autoscalingPolicyIdOnly(self):
    specified_policy = 'cool-policy'
    expected_policy_uri = 'projects/fake-project/regions/global/autoscalingPolicies/cool-policy'

    expected_request_cluster = self.MakeCluster()
    self.AddAutoscalingConfig(expected_request_cluster, expected_policy_uri)
    expected_response_cluster = self.MakeRunningCluster()
    self.AddAutoscalingConfig(expected_response_cluster, expected_policy_uri)
    self.ExpectCreateCalls(
        request_cluster=expected_request_cluster,
        response_cluster=expected_response_cluster)
    result = self.RunDataproc(
        'clusters create {name} --zone={zone} --autoscaling-policy {policy_uri}'
        .format(
            name=self.CLUSTER_NAME, zone=self.ZONE,
            policy_uri=specified_policy))
    self.AssertMessagesEqual(expected_response_cluster, result)

  def testCreateCluster_autoscalingPolicyDifferentProject(self):
    specified_policy = 'projects/another-project/regions/another-region/autoscalingPolicies/cool-policy'

    expected_request_cluster = self.MakeCluster()
    self.AddAutoscalingConfig(expected_request_cluster, specified_policy)
    expected_response_cluster = self.MakeRunningCluster()
    self.AddAutoscalingConfig(expected_response_cluster, specified_policy)
    self.ExpectCreateCalls(
        request_cluster=expected_request_cluster,
        response_cluster=expected_response_cluster)
    result = self.RunDataproc(
        'clusters create {name} --zone={zone} --autoscaling-policy {policy_uri}'
        .format(
            name=self.CLUSTER_NAME, zone=self.ZONE,
            policy_uri=specified_policy))
    self.AssertMessagesEqual(expected_response_cluster, result)


class ClustersCreateUnitTestAlpha(ClustersCreateUnitTestBeta,
                                  base.DataprocTestBaseAlpha):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA

  def testTrack(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope.base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  sdk_test_base.main()
