# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.

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
"""Base classes for container tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import kubeconfig as kconfig
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import config as core_config
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import platforms
from googlecloudsdk.core.util import times
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib.apitools import http_error


class Error(Exception):
  pass


class UnexpectedCallExceptionError(Error):
  """For unexpected calls to mocked functions."""


NOT_FOUND_ERROR = http_error.MakeHttpError(404, 'not found')
UNAUTHORIZED_ERROR = http_error.MakeHttpError(403, 'unauthorized')

FAKE_SDK_BIN_PATH = os.path.join('fake', 'bin', 'path')


def format_date_time(duration):
  """Return RFC3339 string for datetime that is now + given duration.

  Args:
    duration: string ISO 8601 duration, e.g. 'P5D' for period 5 days.

  Returns:
    string timestamp
  """
  # We use a format that preserves +00:00 for UTC to match timestamp format
  # returned by container API.
  fmt = '%Y-%m-%dT%H:%M:%S.%3f%Oz'
  return times.FormatDateTime(
      times.ParseDateTime(duration, tzinfo=times.UTC), fmt=fmt)


class UnitTestBase(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):
  """Base class for all Container tests."""

  COMMAND_BASE = 'container'
  PASSWORD = 'test-password'
  CLUSTER_NAME = 'my-cluster'
  ZONE = 'us-central1-f'
  REGION = 'us-central1'
  PROJECT_ID = 'fake-project-id'
  PROJECT_REF = resources.REGISTRY.Create(
      'container.projects', projectsId=PROJECT_ID)
  PROJECT_NUM = 123456789012
  NUM_NODES = 3
  NODE_POOL_NAME = 'my-pool'
  OPERATION_TARGET = '/projects/{0}/zones/{1}/clusters/{2}'
  TARGET_LINK = 'https://container.googleapis.com/{0}/projects/{1}/zones/{2}/clusters/{3}'  # pylint: disable=line-too-long
  NODE_POOL_TARGET_LINK = 'https://container.googleapis.com/{0}/projects/{1}/zones/{2}/clusters/{3}/nodePools/{4}'  # pylint: disable=line-too-long
  MOCK_OPERATION_ID = 'operation-1414184316101-d4546dd2'
  MOCK_OPERATION_TARGET = OPERATION_TARGET.format(PROJECT_NUM, ZONE,
                                                  CLUSTER_NAME)
  ENDPOINT = '130.211.191.49'
  VERSION = '1.8.0'
  INSTANCE_GROUP_URL = 'https://www.googleapis.com/compute/v1/projects/{0}/zones/{1}/instanceGroupManagers/gke-{2}-group'  # pylint: disable=line-too-long
  MASTER_IPV4_CIDR = '172.16.0.0/28'
  PRIVATE_ENDPOINT = '172.16.0.2'

  def SetUp(self):
    self.MOCK_TARGET_LINK = self.TARGET_LINK.format(  # pylint: disable=invalid-name
        self.API_VERSION, self.PROJECT_NUM, self.ZONE, self.CLUSTER_NAME)
    self.MOCK_NODE_POOL_TARGET_LINK = self.NODE_POOL_TARGET_LINK.format(  # pylint: disable=invalid-name
        self.API_VERSION, self.PROJECT_NUM, self.ZONE, self.CLUSTER_NAME,
        self.NODE_POOL_NAME)
    properties.VALUES.core.project.Set(self.PROJECT_ID)
    self.mocked_client = mock.Client(
        core_apis.GetClientClass('container', self.API_VERSION),
        real_client=core_apis.GetClientInstance(
            'container', self.API_VERSION, no_http=True))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)

    self.mocked_compute_client_v1 = mock.Client(
        core_apis.GetClientClass('compute', 'v1'),
        real_client=core_apis.GetClientInstance('compute', 'v1', no_http=True))
    self.mocked_compute_client_v1.Mock()
    self.addCleanup(self.mocked_compute_client_v1.Unmock)

    # For faster tests
    self.StartPatch('time.sleep')

    # Set/unset envvars that affect kubeconfig behavior to avoid overwriting
    # actual files when running tests locally.
    self.tmp_home = file_utils.TemporaryDirectory()
    self.assertIsNotNone(self.tmp_home.path)
    self.StartDictPatch('os.environ', {'HOME': self.tmp_home.path})
    if os.environ.get('KUBECONFIG'):
      del os.environ['KUBECONFIG']

  def TearDown(self):
    self.tmp_home.Close()

  def Project(self):
    return None

  def _PatchSDKBinPath(self):
    fake_bin_path = self.StartPropertyPatch(core_config.Paths, 'sdk_bin_path')
    fake_bin_path.return_value = FAKE_SDK_BIN_PATH

  def _RunningCluster(self, **kwargs):
    return self._RunningClusterForVersion(self.VERSION, **kwargs)

  def _RunningClusterForVersion(self, version, **kwargs):
    name = kwargs.get('name', self.CLUSTER_NAME)
    defaults = {
        'status': self.running,
        'zone': kwargs.get('zone', self.ZONE),
        'statusMessage': 'Running',
        'endpoint': self.ENDPOINT,
        'clusterApiVersion': version,
        'currentMasterVersion': version,
        'ca_data': 'fakecertificateauthoritydata',
        'key_data': 'fakeclientkeydata',
        'cert_data': 'fakeclientcertificatedata',
        'currentNodeCount': self.NUM_NODES,
        'currentNodeVersion': version,
        'instanceGroupUrls': [
            self._MakeInstanceGroupUrl(self.PROJECT_ID, self.ZONE, name)
        ],
        'maintenancePolicyResourceVersion': 'emptyRV',
    }
    defaults.update(kwargs)
    return self._MakeCluster(**defaults)

  def _RunningClusterWithNodePool(self, **kwargs):
    name = kwargs.get('name', self.CLUSTER_NAME)
    pool_name = kwargs.get('nodePoolName', self.NODE_POOL_NAME)
    zone = kwargs.get('zone', self.ZONE)
    defaults = {
        'name':
            name,
        'nodePoolName':
            pool_name,
        'instanceGroupUrls': [
            self._MakeInstanceGroupUrl(self.PROJECT_ID, zone, name, pool_name)
        ],
    }
    defaults.update(kwargs)
    return self._RunningCluster(**defaults)

  def _RunningPrivateCluster(self, **kwargs):
    master_ipv4_cidr = kwargs.get('masterIpv4Cidr', self.MASTER_IPV4_CIDR)
    private_endpoint = kwargs.get('privateEndpoint', self.PRIVATE_ENDPOINT)
    config = self._MakePrivateClusterConfig(
        enablePrivateNodes=True,
        enablePrivateEndpoint=False,
        masterIpv4Cidr=master_ipv4_cidr,
    )
    config.privateEndpoint = private_endpoint
    defaults = {'privateClusterConfig': config}
    defaults.update(kwargs)
    return self._RunningCluster(**defaults)

  def _TestDefaultAuth(self, c_config):
    self._TestGcloudCredentials(c_config)

  def _TestGcloudCredentials(self, c_config):
    kubeconfig = kconfig.Kubeconfig.Default()
    self.assertIsNotNone(c_config)
    self.assertTrue(c_config.has_ca_cert)
    self.assertIsNotNone(c_config.auth_provider)
    self.assertEqual(c_config.auth_provider.get('name'), 'gcp')
    bin_name = 'gcloud'
    if platforms.OperatingSystem.IsWindows():
      bin_name = 'gcloud.cmd'
    self.assertDictEqual(
        kubeconfig.users[c_config.kube_context]['user']['auth-provider'], {
            'name': 'gcp',
            'config': {
                'cmd-path': os.path.join(FAKE_SDK_BIN_PATH, bin_name),
                'cmd-args': 'config config-helper --format=json',
                'token-key': '{.credential.access_token}',
                'expiry-key': '{.credential.token_expiry}',
            }
        })
    self.assertTrue(c_config.has_ca_cert)

  def _TestAppDefaultCredentials(self, c_config):
    kubeconfig = kconfig.Kubeconfig.Default()
    self.assertIsNotNone(c_config)
    self.assertTrue(c_config.has_ca_cert)
    self.assertIsNotNone(c_config.auth_provider)
    self.assertEqual(c_config.auth_provider.get('name'), 'gcp')
    self.assertDictEqual(
        kubeconfig.users[c_config.kube_context]['user']['auth-provider'],
        {'name': 'gcp'})
    self.assertTrue(c_config.has_ca_cert)


class TestBase(cli_test_base.CliTestBase):
  """Mixin class for testing."""

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('container', self.API_VERSION)
    self.compute_messages = core_apis.GetMessagesModule('compute', 'v1')
    self.op_delete = self.messages.Operation.OperationTypeValueValuesEnum.DELETE_CLUSTER  # pylint: disable=line-too-long
    self.op_create = self.messages.Operation.OperationTypeValueValuesEnum.CREATE_CLUSTER  # pylint: disable=line-too-long
    self.op_done = self.messages.Operation.StatusValueValuesEnum.DONE
    self.op_pending = self.messages.Operation.StatusValueValuesEnum.PENDING
    self.op_abort = self.messages.Operation.StatusValueValuesEnum.ABORTING
    self.op_upgrade_nodes = self.messages.Operation.OperationTypeValueValuesEnum.UPGRADE_NODES  # pylint: disable=line-too-long
    self.op_upgrade_master = self.messages.Operation.OperationTypeValueValuesEnum.UPGRADE_MASTER  # pylint: disable=line-too-long
    self.op_update_cluster = self.messages.Operation.OperationTypeValueValuesEnum.UPDATE_CLUSTER  # pylint: disable=line-too-long
    self.op_set_master_auth = self.messages.Operation.OperationTypeValueValuesEnum.SET_MASTER_AUTH  # pylint: disable=line-too-long
    self.op_set_labels = self.messages.Operation.OperationTypeValueValuesEnum.SET_LABELS  # pylint: disable=line-too-long
    self.compute_op_done = self.compute_messages.Operation.StatusValueValuesEnum.DONE  # pylint: disable=line-too-long
    self.compute_op_pending = self.compute_messages.Operation.StatusValueValuesEnum.PENDING  # pylint: disable=line-too-long
    self.provisioning = self.messages.Cluster.StatusValueValuesEnum.PROVISIONING
    self.stopping = self.messages.Cluster.StatusValueValuesEnum.STOPPING
    self.running = self.messages.Cluster.StatusValueValuesEnum.RUNNING
    self.error = self.messages.Cluster.StatusValueValuesEnum.ERROR
    self.reconciling = self.messages.Cluster.StatusValueValuesEnum.RECONCILING
    self.degraded = self.messages.Cluster.StatusValueValuesEnum.DEGRADED
    self.action_set_password = self.messages.SetMasterAuthRequest.ActionValueValuesEnum.SET_PASSWORD  # pylint: disable=line-too-long
    self.action_generate_password = self.messages.SetMasterAuthRequest.ActionValueValuesEnum.GENERATE_PASSWORD  # pylint: disable=line-too-long
    self.action_set_username = self.messages.SetMasterAuthRequest.ActionValueValuesEnum.SET_USERNAME  # pylint: disable=line-too-long

  def _MakeCluster(self, **kwargs):
    # Avoid side effects by copying all these args. This ensures that when we
    # modify parts of a message, it won't affect the original objects that were
    # passed in, allowing them to be reused in calls that might depend on them
    # not having been changed (which is especially dangerous given that we make
    # all these Expect... calls that are not actually checked until after we
    # declare them all!).
    kwargs = copy.deepcopy(kwargs)

    # Construct the default pool, if we don't have any passed in. We
    # can't know all the possible permutations, so any tests involving
    # multiple nodepools must construct them prior to _MakeCluster.
    if kwargs.get('nodePools') is None:
      pool = self._MakeDefaultNodePool(**kwargs)
      kwargs['nodePools'] = [pool]
      kwargs['instanceGroupUrls'] = pool.instanceGroupUrls

    c = self.messages.Cluster(
        name=kwargs.get('name', self.CLUSTER_NAME),
        currentNodeCount=kwargs.get('currentNodeCount'),
        initialNodeCount=kwargs.get('initialNodeCount'),
        locations=kwargs.get('locations', []),
        endpoint=kwargs.get('endpoint'),
        status=kwargs.get('status'),
        statusMessage=kwargs.get('statusMessage'),
        zone=kwargs.get('zone'),
        initialClusterVersion=kwargs.get('clusterApiVersion'),
        currentMasterVersion=kwargs.get('currentMasterVersion'),
        network=kwargs.get('network'),
        subnetwork=kwargs.get('subnetwork'),
        loggingService=kwargs.get('loggingService'),
        monitoringService=kwargs.get('monitoringService'),
        clusterIpv4Cidr=kwargs.get('clusterIpv4Cidr'),
        currentNodeVersion=kwargs.get('currentNodeVersion'),
        instanceGroupUrls=kwargs.get('instanceGroupUrls', []),
        addonsConfig=kwargs.get('addonsConfig'),
        nodePools=kwargs.get('nodePools'),
        nodeConfig=kwargs.get('nodeConfig'),
        binaryAuthorization=kwargs.get('binaryAuthorization'),
        enableKubernetesAlpha=kwargs.get('enableKubernetesAlpha'),
        expireTime=kwargs.get('expireTime'),
        selfLink=kwargs.get('selfLink'),
        masterAuthorizedNetworksConfig=kwargs.get('authorizedNetworks'),
        legacyAbac=kwargs.get('legacyAbac'),
        resourceLabels=kwargs.get('labels'),
        maintenancePolicy=kwargs.get('maintenancePolicy'),
        privateClusterConfig=kwargs.get('privateClusterConfig'),
        defaultMaxPodsConstraint=kwargs.get('defaultMaxPodsConstraint'),
        enableTpu=kwargs.get('enableTpu'),
        verticalPodAutoscaling=kwargs.get('verticalPodAutoscaling'),
        autoscaling=kwargs.get('clusterAutoscaling'),
    )
    if kwargs.get('conditions'):
      c.conditions.extend(kwargs.get('conditions'))
    if (kwargs.get('issueClientCertificate') is not None or
        kwargs.get('username') is not None or
        kwargs.get('password') is not None or
        kwargs.get('ca_data') is not None or
        kwargs.get('key_data') is not None or
        kwargs.get('cert_data') is not None):
      c.masterAuth = self.messages.MasterAuth(
          password=kwargs.get('password'),
          username=kwargs.get('username'),
          clusterCaCertificate=kwargs.get('ca_data'),
          clientKey=kwargs.get('key_data'),
          clientCertificate=kwargs.get('cert_data'),
      )
      if kwargs.get('issueClientCertificate') is not None:
        c.masterAuth.clientCertificateConfig = (
            self.messages.ClientCertificateConfig(
                issueClientCertificate=kwargs.get('issueClientCertificate')))

    # Initialize maintenance policy resource version if told to. We can't do
    # this all the time because it's something the server sets. So normally all
    # get requests will have it, but we shouldn't be setting ourselves for
    # create requests.
    resource_version = kwargs.get('maintenancePolicyResourceVersion')
    if resource_version:
      if c.maintenancePolicy is None:
        c.maintenancePolicy = self.messages.MaintenancePolicy()
      if not c.maintenancePolicy.resourceVersion:
        c.maintenancePolicy.resourceVersion = resource_version

    if kwargs.get('databaseEncryptionKey'):
      c.databaseEncryption = self.messages.DatabaseEncryption(
          keyName=kwargs.get('databaseEncryptionKey'),
          state=self.messages.DatabaseEncryption.StateValueValuesEnum.ENCRYPTED)
    return c

  def _MakeClusterWithAutoscaling(self, **kwargs):
    pool = self.messages.NodePool(autoscaling=kwargs.get('autoscaling'))
    kwargs['nodePools'] = [pool]
    return self._MakeCluster(**kwargs)

  def _MakeDefaultNodePool(self, **kwargs):
    pool_args = kwargs.copy()
    pool_args['name'] = kwargs.get('nodePoolName', 'default-pool')
    return self._MakeNodePool(**pool_args)

  def _MakeNodePool(self, **kwargs):
    return self.messages.NodePool(
        name=kwargs.get('name', self.NODE_POOL_NAME),
        version=kwargs.get('nodeVersion'),
        initialNodeCount=kwargs.get('initialNodeCount', self.NUM_NODES),
        config=self.messages.NodeConfig(
            diskSizeGb=kwargs.get('diskSizeGb'),
            diskType=kwargs.get('diskType'),
            machineType=kwargs.get('machineType'),
            oauthScopes=kwargs.get('oauthScopes', self._DEFAULT_SCOPES),
            localSsdCount=kwargs.get('localSsdCount'),
            tags=kwargs.get('tags', []),
            labels=kwargs.get('nodeLabels'),
            imageType=kwargs.get('imageType'),
            nodeImageConfig=kwargs.get('nodeImageConfig'),
            preemptible=kwargs.get('preemptible'),
            serviceAccount=kwargs.get('serviceAccount'),
            accelerators=kwargs.get('accelerators', []),
            minCpuPlatform=kwargs.get('minCpuPlatform'),
            taints=kwargs.get('nodeTaints', []),
            metadata=kwargs.get('metadata'),
            shieldedInstanceConfig=kwargs.get('shieldedInstanceConfig'),
        ),
        instanceGroupUrls=kwargs.get('instanceGroupUrls', []),
        autoscaling=kwargs.get('autoscaling'),
        management=(kwargs.get('management') if 'management' in kwargs else
                    self._MakeDefaultNodeManagement()),
        maxPodsConstraint=kwargs.get('maxPodsConstraint'),
    )

  # Creates a default node management adaptive to release tracks.
  # Autorepair default value is True for default image config.
  # Autoupgrade default value is True.
  def _MakeDefaultNodeManagement(self, auto_repair=True):
    return self.messages.NodeManagement(
        autoRepair=auto_repair, autoUpgrade=True)

  def _MakeDefaultUpgradeSettings(self):
    if self.API_VERSION == 'v1':
      return None
    return self.messages.UpgradeSettings(maxSurge=1)

  def _MakeIPAllocationPolicy(self, **kwargs):
    policy = self.messages.IPAllocationPolicy()
    if 'useIpAliases' in kwargs:
      policy.useIpAliases = kwargs['useIpAliases']
    if 'createSubnetwork' in kwargs:
      policy.createSubnetwork = kwargs['createSubnetwork']
    if 'subnetworkName' in kwargs:
      policy.subnetworkName = kwargs['subnetworkName']
    if 'clusterIpv4Cidr' in kwargs:
      policy.clusterIpv4CidrBlock = kwargs['clusterIpv4Cidr']
    if 'nodeIpv4Cidr' in kwargs:
      policy.nodeIpv4CidrBlock = kwargs['nodeIpv4Cidr']
    if 'servicesIpv4Cidr' in kwargs:
      policy.servicesIpv4CidrBlock = kwargs['servicesIpv4Cidr']
    if 'tpuIpv4Cidr' in kwargs:
      policy.tpuIpv4CidrBlock = kwargs['tpuIpv4Cidr']
    if 'tpuUseServiceNetworking' in kwargs:
      policy.tpuUseServiceNetworking = kwargs['tpuUseServiceNetworking']
    if 'clusterSecondaryRangeName' in kwargs:
      policy.clusterSecondaryRangeName = kwargs['clusterSecondaryRangeName']
    if 'servicesSecondaryRangeName' in kwargs:
      policy.servicesSecondaryRangeName = kwargs['servicesSecondaryRangeName']
    return policy

  def _MakePrivateClusterConfig(self, **kwargs):
    config = self.messages.PrivateClusterConfig()
    if 'enablePeeringRouteSharing' in kwargs:
      config.enablePeeringRouteSharing = kwargs['enablePeeringRouteSharing']
    if 'enablePrivateNodes' in kwargs:
      config.enablePrivateNodes = kwargs['enablePrivateNodes']
    if 'enablePrivateEndpoint' in kwargs:
      config.enablePrivateEndpoint = kwargs['enablePrivateEndpoint']
    if 'masterIpv4Cidr' in kwargs:
      config.masterIpv4CidrBlock = kwargs['masterIpv4Cidr']
    return config

  def _ServerConfig(self):
    return self.messages.ServerConfig(defaultClusterVersion=self.VERSION)

  def _MakeOperation(self, **kwargs):
    status = kwargs.get('errorMessage', kwargs.get('statusMessage'))
    return self.messages.Operation(
        statusMessage=status,
        name=kwargs.get('name', self.MOCK_OPERATION_ID),
        operationType=kwargs.get('operationType', self.op_create),
        status=kwargs.get('status', self.op_pending),
        targetLink=kwargs.get('targetLink', self.MOCK_TARGET_LINK),
        zone=kwargs.get('zone', self.ZONE),
        detail=kwargs.get('detail'),
    )

  def _MakeNodePoolOperation(self, **kwargs):
    status = kwargs.get('errorMessage', kwargs.get('statusMessage'))
    return self.messages.Operation(
        statusMessage=status,
        name=kwargs.get('name', self.MOCK_OPERATION_ID),
        operationType=kwargs.get('operationType', self.op_create),
        status=kwargs.get('status', self.op_pending),
        targetLink=kwargs.get('targetLink', self.MOCK_NODE_POOL_TARGET_LINK),
        zone=kwargs.get('zone', self.ZONE),
    )

  def _MakeComputeOperation(self, **kwargs):
    return self.compute_messages.Operation(
        statusMessage=kwargs.get('errorMessage'),
        name=kwargs.get('name', self.MOCK_OPERATION_ID),
        operationType=kwargs.get('operationType', 'update'),
        status=kwargs.get('status', self.compute_op_done),
        targetLink=kwargs.get('targetLink', self.MOCK_TARGET_LINK),
        zone=kwargs.get('zone', self.ZONE),
    )

  def _MakeInstanceGroupUrl(self, project, zone, cluster_name, pool_name=None):
    igm = cluster_name
    if pool_name:
      igm += '-' + pool_name
    return self.INSTANCE_GROUP_URL.format(project, zone, igm)

  def _MakeUpgradeSettings(self, **kwargs):
    settings = self.messages.UpgradeSettings()
    if 'maxSurge' in kwargs:
      settings.maxSurge = kwargs['maxSurge']
    if 'maxUnavailable' in kwargs:
      settings.maxUnavailable = kwargs['maxUnavailable']
    return settings

  def ExpectGetCluster(self, cluster, exception=None, zone=None):
    raise NotImplementedError('ExpectGetCluster is not overridden')

  def ExpectCreateCluster(self,
                          cluster,
                          response=None,
                          exception=None,
                          zone=None):
    raise NotImplementedError('ExpectCreateCluster is not overridden')

  def ExpectDeleteCluster(self,
                          cluster_name,
                          response=None,
                          exception=None,
                          zone=None):
    raise NotImplementedError('ExpectDeleteCluster is not overridden')

  def ExpectListClusters(self,
                         clusters,
                         zone=None,
                         project_id=None,
                         missing=None):
    raise NotImplementedError('ExpectListClusters is not overridden')

  def ExpectGetOperation(self, response, exception=None):
    raise NotImplementedError('ExpectGetOperation is not overridden')

  def ExpectListOperation(self, response, exception=None):
    raise NotImplementedError('ExpectListOperation is not overridden')

  def ExpectResize(self, cluster, size, ig):
    group = os.path.basename(ig)
    op = self._MakeComputeOperation(name='resize_' + group)
    self.mocked_compute_client_v1.instanceGroupManagers.Resize.Expect(
        self.compute_messages.ComputeInstanceGroupManagersResizeRequest(
            instanceGroupManager=group,
            project=self.PROJECT_ID,
            zone=cluster.zone,
            size=size), op)
    return op

  def ExpectResizeNodePool(self,
                           node_pool_name,
                           size,
                           response=None,
                           exception=None,
                           zone=None):
    raise NotImplementedError('ExpectResizeNodePool is not overridden')

  def ExpectCreateNodePool(self,
                           node_pool,
                           response=None,
                           exception=None,
                           zone=None):
    raise NotImplementedError('ExpectCreateNodePool is not overridden')

  def ExpectGetNodePool(self,
                        node_pool_id,
                        response=None,
                        exception=None,
                        zone=None):
    raise NotImplementedError('ExpectGetNodePool is not overridden')

  def ExpectDeleteNodePool(self,
                           node_pool_name,
                           response=None,
                           exception=None,
                           zone=None):
    raise NotImplementedError('ExpectDeleteNodePool is not overridden')

  def ExpectSetNodePoolManagement(self,
                                  node_pool_name,
                                  node_management,
                                  response=None,
                                  exception=None,
                                  zone=None):
    raise NotImplementedError('ExpectSetNodePoolManagement is not overridden')

  def ExpectUpdateNodePool(self,
                           node_pool_name,
                           workload_metadata_config=None,
                           locations=None,
                           response=None,
                           exception=None,
                           zone=None,
                           upgrade_settings=None):
    raise NotImplementedError('ExpectUpdateNodePool is not overridden')

  def _MakeListNodePoolsResponse(self, node_pools):
    return self.messages.ListNodePoolsResponse(nodePools=node_pools)

  def ExpectListNodePools(self,
                          project_id=None,
                          response=None,
                          exception=None,
                          zone=None):
    raise NotImplementedError('ExpectListNodePools is not overridden')

  def ExpectRollbackOperation(self,
                              node_pool_name,
                              response=None,
                              exception=None,
                              zone=None):
    raise NotImplementedError('ExpectRollbackOperation is not overridden')

  def ExpectCancelOperation(self, op=None, exception=None):
    raise NotImplementedError('ExpectCancelOperation is not overridden')

  def ExpectSetLabels(self,
                      cluster_name,
                      resource_labels,
                      fingerprint,
                      response=None,
                      zone=None):
    raise NotImplementedError('ExpectSetLabels is not overridden')

  def ExpectUpgradeCluster(self, cluster_name, update, response, location=None):
    raise NotImplementedError('ExpectUpgradeCluster is not overridden')

  def ExpectUpdateCluster(self, cluster_name, update, response):
    raise NotImplementedError('ExpectUpdateCluster is not overridden')

  def ExpectSetMasterAuth(self, cluster_name, action, update, response):
    raise NotImplementedError('ExpectSetMasterAuth is not overridden')

  def ExpectLegacyAbac(self, cluster_name, enabled, response):
    raise NotImplementedError('ExpectLegacyAbac is not overridden')

  def ExpectStartIpRotation(self, cluster_name, response=None, exception=None):
    raise NotImplementedError('ExpectStartIpRotation is not overridden')

  def ExpectCompleteIpRotation(self,
                               cluster_name,
                               response=None,
                               exception=None):
    raise NotImplementedError('ExpectCompleteIpRotation is not overridden')

  def ExpectSetNetworkPolicy(self, cluster_name, enabled=True, response=None):
    raise NotImplementedError('ExpectSetNetworkPolicy is not overridden')

  def ExpectSetLoggingService(self,
                              cluster_name,
                              logging_service,
                              response=None,
                              exception=None):
    raise NotImplementedError('ExpectSetLoggingService is not overridden')

  def ExpectSetMaintenanceWindow(self,
                                 cluster_name,
                                 policy=None,
                                 response=None):
    raise NotImplementedError('ExpectSetMaintenanceWindow is not overridden')

  def ExpectGetServerConfig(self, location, exception=None):
    raise NotImplementedError('ExpectGetServerConfig is not overridden')


class GATestBase(TestBase):
  """Mixin class for testing v1."""
  API_VERSION = 'v1'

  # Sort the scopes to assert equality of the lists
  _DEFAULT_SCOPES = sorted([
      'https://www.googleapis.com/auth/devstorage.read_only',
      'https://www.googleapis.com/auth/logging.write',
      'https://www.googleapis.com/auth/monitoring',
      'https://www.googleapis.com/auth/service.management.readonly',
      'https://www.googleapis.com/auth/servicecontrol',
      'https://www.googleapis.com/auth/trace.append',
  ])

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def ExpectCreateCluster(self,
                          cluster,
                          response=None,
                          exception=None,
                          zone=None):
    if not zone:
      zone = self.ZONE
    self.mocked_client.projects_locations_clusters.Create.Expect(
        self.messages.CreateClusterRequest(
            cluster=cluster,
            parent=api_adapter.ProjectLocation(self.PROJECT_ID, zone)),
        response=response,
        exception=exception)

  def ExpectDeleteCluster(self,
                          cluster_name,
                          response=None,
                          exception=None,
                          zone=None):
    if not zone:
      zone = self.ZONE
    self.mocked_client.projects_locations_clusters.Delete.Expect(
        self.messages.ContainerProjectsLocationsClustersDeleteRequest(
            name=api_adapter.ProjectLocationCluster(self.PROJECT_ID, zone,
                                                    cluster_name)),
        response=response,
        exception=exception)

  def ExpectGetCluster(self, cluster, exception=None, zone=None):
    if not zone:
      zone = self.ZONE
    if exception:
      response = None
    else:
      response = cluster
    self.mocked_client.projects_locations_clusters.Get.Expect(
        self.messages.ContainerProjectsLocationsClustersGetRequest(
            # use the response operation name/zone same as request
            name=api_adapter.ProjectLocationCluster(self.PROJECT_ID, zone,
                                                    cluster.name)),
        response,
        exception=exception)

  def ExpectListClusters(self,
                         clusters,
                         zone=None,
                         project_id=None,
                         missing=None):
    if not project_id:
      project_id = self.PROJECT_ID
    if not zone:
      zone = '-'
    if not missing:
      missing = []
    self.mocked_client.projects_locations_clusters.List.Expect(
        self.messages.ContainerProjectsLocationsClustersListRequest(
            parent=api_adapter.ProjectLocation(project_id, zone)),
        self.messages.ListClustersResponse(
            clusters=clusters, missingZones=missing))

  def ExpectCreateNodePool(self,
                           node_pool,
                           response=None,
                           exception=None,
                           zone=None):
    if not zone:
      zone = self.ZONE
    self.mocked_client.projects_locations_clusters_nodePools.Create.Expect(
        self.messages.CreateNodePoolRequest(
            parent=api_adapter.ProjectLocationCluster(self.PROJECT_ID, zone,
                                                      self.CLUSTER_NAME),
            nodePool=node_pool),
        response=response,
        exception=exception)

  # TODO(b/64575339) Make this work more like GetCluster (specifically, infer
  # node_pool_id from node_pool (response).
  def ExpectGetNodePool(self,
                        node_pool_id,
                        response=None,
                        exception=None,
                        zone=None):
    if not zone:
      zone = self.ZONE
    self.mocked_client.projects_locations_clusters_nodePools.Get.Expect(
        self.messages.ContainerProjectsLocationsClustersNodePoolsGetRequest(
            # use the response operation name/zone same as request
            name=api_adapter.ProjectLocationClusterNodePool(
                self.PROJECT_ID, zone, self.CLUSTER_NAME, node_pool_id)),
        response=response,
        exception=exception)

  def ExpectDeleteNodePool(self,
                           node_pool_name,
                           response=None,
                           exception=None,
                           zone=None):
    if not zone:
      zone = self.ZONE
    self.mocked_client.projects_locations_clusters_nodePools.Delete.Expect(
        self.messages.ContainerProjectsLocationsClustersNodePoolsDeleteRequest(
            name=api_adapter.ProjectLocationClusterNodePool(
                self.PROJECT_ID, zone, self.CLUSTER_NAME, node_pool_name)),
        response=response,
        exception=exception)

  def ExpectSetNodePoolManagement(self,
                                  node_pool_name,
                                  node_management,
                                  response=None,
                                  exception=None,
                                  zone=None):
    if not zone:
      zone = self.ZONE
    (self.mocked_client.projects_locations_clusters_nodePools.SetManagement
     .Expect(
         self.messages.SetNodePoolManagementRequest(
             name=api_adapter.ProjectLocationClusterNodePool(
                 self.PROJECT_ID, zone, self.CLUSTER_NAME, node_pool_name),
             management=node_management),
         response=response,
         exception=exception))

  def ExpectUpdateNodePool(self,
                           node_pool_name,
                           workload_metadata_config=None,
                           locations=None,
                           response=None,
                           exception=None,
                           zone=None,
                           upgrade_settings=None):
    if not zone:
      zone = self.ZONE
    if locations is None:
      locations = []
    msg = self.messages.UpdateNodePoolRequest(
        name=api_adapter.ProjectLocationClusterNodePool(self.PROJECT_ID, zone,
                                                        self.CLUSTER_NAME,
                                                        node_pool_name),
        workloadMetadataConfig=workload_metadata_config,
        locations=locations)
    self.mocked_client.projects_locations_clusters_nodePools.Update.Expect(
        msg, response=response, exception=exception)

  def ExpectListNodePools(self, response=None, exception=None, zone=None):
    if not zone:
      zone = self.ZONE
    self.mocked_client.projects_locations_clusters_nodePools.List.Expect(
        self.messages.ContainerProjectsLocationsClustersNodePoolsListRequest(
            parent=api_adapter.ProjectLocationCluster(self.PROJECT_ID, zone,
                                                      self.CLUSTER_NAME)),
        response=response,
        exception=exception)

  def ExpectResizeNodePool(self,
                           node_pool_name,
                           size,
                           response=None,
                           exception=None,
                           zone=None):
    if not zone:
      zone = self.ZONE
    req = self.messages.SetNodePoolSizeRequest(
        name=api_adapter.ProjectLocationClusterNodePool(self.PROJECT_ID, zone,
                                                        self.CLUSTER_NAME,
                                                        node_pool_name),
        nodeCount=size)
    self.mocked_client.projects_locations_clusters_nodePools.SetSize.Expect(
        req, response=response, exception=exception)

  def ExpectRollbackOperation(self,
                              node_pool_name,
                              response=None,
                              exception=None,
                              zone=None):
    if not zone:
      zone = self.ZONE
    self.mocked_client.projects_locations_clusters_nodePools.Rollback.Expect(
        self.messages.RollbackNodePoolUpgradeRequest(
            name=api_adapter.ProjectLocationClusterNodePool(
                self.PROJECT_ID, zone, self.CLUSTER_NAME, node_pool_name)),
        response=response,
        exception=exception)

  def ExpectGetOperation(self, response, exception=None):
    # use the response operation name/zone same as request
    req = self.messages.ContainerProjectsLocationsOperationsGetRequest(
        name=api_adapter.ProjectLocationOperation(self.PROJECT_ID,
                                                  response.zone, response.name))
    if exception:
      response = None
    self.mocked_client.projects_locations_operations.Get.Expect(
        req, response=response, exception=exception)

  def ExpectListOperation(self, zone, response, exception=None):
    req = self.messages.ContainerProjectsLocationsOperationsListRequest(
        parent=api_adapter.ProjectLocation(self.PROJECT_ID, zone))
    if exception:
      response = None
    self.mocked_client.projects_locations_operations.List.Expect(
        req, response=response, exception=exception)

  def ExpectCancelOperation(self, op=None, exception=None):
    self.mocked_client.projects_locations_operations.Cancel.Expect(
        self.messages.CancelOperationRequest(
            name=api_adapter.ProjectLocationOperation(self.PROJECT_ID,
                                                      self.ZONE, op.name)),
        response=self.messages.Empty(),
        exception=exception)

  def ExpectSetLabels(self,
                      cluster_name,
                      resource_labels,
                      fingerprint,
                      response=None,
                      zone=None):
    if not zone:
      zone = self.ZONE
    self.mocked_client.projects_locations_clusters.SetResourceLabels.Expect(
        self.messages.SetLabelsRequest(
            name=api_adapter.ProjectLocationCluster(self.PROJECT_ID, zone,
                                                    cluster_name),
            resourceLabels=resource_labels,
            labelFingerprint=fingerprint), response)

  def ExpectUpgradeCluster(self, cluster_name, update, response, location=None):
    if not location:
      location = self.ZONE
    self.mocked_client.projects_locations_clusters.Update.Expect(
        self.msgs.UpdateClusterRequest(
            name=api_adapter.ProjectLocationCluster(self.PROJECT_ID, location,
                                                    cluster_name),
            update=update),
        response=response)

  def ExpectUpdateCluster(self, cluster_name, update, response):
    self.mocked_client.projects_locations_clusters.Update.Expect(
        self.msgs.UpdateClusterRequest(
            name=api_adapter.ProjectLocationCluster(self.PROJECT_ID, self.ZONE,
                                                    cluster_name),
            update=update),
        response=response)

  def ExpectSetMasterAuth(self,
                          cluster_name,
                          action,
                          update,
                          response=None,
                          exception=None):
    self.mocked_client.projects_locations_clusters.SetMasterAuth.Expect(
        self.msgs.SetMasterAuthRequest(
            name=api_adapter.ProjectLocationCluster(self.PROJECT_ID, self.ZONE,
                                                    cluster_name),
            action=action,
            update=update),
        response=response,
        exception=exception)

  def ExpectLegacyAbac(self, cluster_name, enabled, response):
    self.mocked_client.projects_locations_clusters.SetLegacyAbac.Expect(
        self.msgs.SetLegacyAbacRequest(
            name=api_adapter.ProjectLocationCluster(self.PROJECT_ID, self.ZONE,
                                                    cluster_name),
            enabled=enabled),
        response=response)

  def ExpectStartIpRotation(self,
                            cluster_name,
                            rotate_credentials=False,
                            response=None,
                            exception=None):
    self.mocked_client.projects_locations_clusters.StartIpRotation.Expect(
        self.msgs.StartIPRotationRequest(
            name=api_adapter.ProjectLocationCluster(self.PROJECT_ID, self.ZONE,
                                                    cluster_name),
            rotateCredentials=rotate_credentials),
        response=response,
        exception=exception)

  def ExpectCompleteIpRotation(self,
                               cluster_name,
                               response=None,
                               exception=None):
    self.mocked_client.projects_locations_clusters.CompleteIpRotation.Expect(
        self.msgs.CompleteIPRotationRequest(
            name=api_adapter.ProjectLocationCluster(self.PROJECT_ID, self.ZONE,
                                                    cluster_name)),
        response=response,
        exception=exception)

  def ExpectSetNetworkPolicy(self, cluster_name, enabled=True, response=None):
    self.mocked_client.projects_locations_clusters.SetNetworkPolicy.Expect(
        self.msgs.SetNetworkPolicyRequest(
            name=api_adapter.ProjectLocationCluster(self.PROJECT_ID, self.ZONE,
                                                    cluster_name),
            networkPolicy=self.msgs.NetworkPolicy(
                enabled=enabled,
                provider=self.msgs.NetworkPolicy.ProviderValueValuesEnum.CALICO)
        ),
        response=response)

  def ExpectSetLoggingService(self,
                              cluster_name,
                              logging_service,
                              response=None,
                              exception=None):
    self.mocked_client.projects_locations_clusters.SetLogging.Expect(
        self.msgs.SetLoggingServiceRequest(
            name=api_adapter.ProjectLocationCluster(self.PROJECT_ID, self.ZONE,
                                                    cluster_name),
            loggingService=logging_service),
        response=response,
        exception=exception)

  def ExpectSetMaintenancePolicy(self,
                                 cluster_name,
                                 policy=None,
                                 response=None):
    self.mocked_client.projects_locations_clusters.SetMaintenancePolicy.Expect(
        self.msgs.SetMaintenancePolicyRequest(
            name=api_adapter.ProjectLocationCluster(self.PROJECT_ID, self.ZONE,
                                                    cluster_name),
            maintenancePolicy=policy),
        response=response)

  def ExpectGetServerConfig(self, location, exception=None):
    if exception:
      response = None
    else:
      response = self.messages.ServerConfig(
          defaultClusterVersion='1.2.3', validMasterVersions=['1.3.2'])
    self.mocked_client.projects_locations.GetServerConfig.Expect(
        self.messages.ContainerProjectsLocationsGetServerConfigRequest(
            name=api_adapter.ProjectLocation(self.PROJECT_ID, location)),
        response=response,
        exception=exception)

  def _MakeUsableSubnetworkSecondaryRange(self, **kwargs):
    return self.messages.UsableSubnetworkSecondaryRange(
        rangeName=kwargs.get('rangeName'),
        ipCidrRange=kwargs.get('ipCidrRange'),
        status=kwargs.get('status'))

  def _MakeUsableSubnet(self, **kwargs):
    network = resources.REGISTRY.Create(
        'compute.networks',
        project=self.PROJECT_ID,
        network=kwargs.get('network'))
    subnetwork = resources.REGISTRY.Create(
        'compute.subnetworks',
        project=self.PROJECT_ID,
        region=self.REGION,
        subnetwork=kwargs.get('subnetwork'))
    return self.messages.UsableSubnetwork(
        subnetwork=subnetwork.RelativeName(),
        network=network.RelativeName(),
        ipCidrRange=kwargs.get('ipCidrRange'),
        secondaryIpRanges=kwargs.get('secondaryIpRanges', []),
        statusMessage=kwargs.get('statusMessage'))

  def _MakeListUsableSubnetworksResponse(self, subnets):
    return self.messages.ListUsableSubnetworksResponse(subnetworks=subnets)

  def _ExpectListUsableSubnets(self, response, exception=None):
    req = self.messages.ContainerProjectsAggregatedUsableSubnetworksListRequest(
        parent=self.PROJECT_REF.RelativeName(), pageSize=500, filter='')
    if exception:
      response = None
    self.mocked_client.projects_aggregated_usableSubnetworks.List.Expect(
        req, response=response, exception=exception)


class BetaTestBase(GATestBase):
  """Mixin class for testing v1beta1."""
  API_VERSION = 'v1beta1'

  # Sort the scopes to assert equality of the lists
  _DEFAULT_SCOPES = sorted([
      'https://www.googleapis.com/auth/devstorage.read_only',
      'https://www.googleapis.com/auth/logging.write',
      'https://www.googleapis.com/auth/monitoring',
      'https://www.googleapis.com/auth/service.management.readonly',
      'https://www.googleapis.com/auth/servicecontrol',
      'https://www.googleapis.com/auth/trace.append',
  ])

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _MakeCluster(self, **kwargs):
    cluster = GATestBase._MakeCluster(self, **kwargs)
    cluster.verticalPodAutoscaling = kwargs.get('verticalPodAutoscaling')
    cluster.shieldedNodes = kwargs.get('shieldedNodes')
    if kwargs.get('databaseEncryptionKey'):
      cluster.databaseEncryption = self.messages.DatabaseEncryption(
          keyName=kwargs.get('databaseEncryptionKey'),
          state=self.messages.DatabaseEncryption.StateValueValuesEnum.ENCRYPTED)
    cluster.releaseChannel = kwargs.get('releaseChannel')

    return cluster

  def _MakeNodePool(self, **kwargs):
    node_pool = GATestBase._MakeNodePool(self, **kwargs)
    node_pool.config.workloadMetadataConfig = kwargs.get(
        'workloadMetadataConfig')
    node_pool.config.metadata = kwargs.get('metadata')
    node_pool.config.sandboxConfig = kwargs.get('sandboxConfig')
    if kwargs.get('nodePoolLocations'):
      node_pool.locations = kwargs.get('nodePoolLocations')
    if 'upgradeSettings' in kwargs:
      node_pool.upgradeSettings = kwargs.get('upgradeSettings')
    else:
      node_pool.upgradeSettings = self._MakeDefaultUpgradeSettings()
    return node_pool

  def _MakeIPAllocationPolicy(self, **kwargs):
    policy = GATestBase._MakeIPAllocationPolicy(self, **kwargs)
    if 'allowRouteOverlap' in kwargs:
      policy.allowRouteOverlap = kwargs.get('allowRouteOverlap')
    return policy

  def _MakeUsableSubnetworkSecondaryRange(self, **kwargs):
    return self.messages.UsableSubnetworkSecondaryRange(
        rangeName=kwargs.get('rangeName'),
        ipCidrRange=kwargs.get('ipCidrRange'),
        status=kwargs.get('status'))

  def _MakeUsableSubnet(self, **kwargs):
    # Construct the default pool, if we don't have any passed in. We
    # can't know all the possible permutations, so any tests involving
    # multiple nodepools must construct them prior to _MakeCluster.
    # if kwargs.get('nodePools') is None:
    #   pool = self._MakeDefaultNodePool(**kwargs)
    #   kwargs['nodePools'] = [pool]
    #   kwargs['instanceGroupUrls'] = pool.instanceGroupUrls
    network = resources.REGISTRY.Create(
        'compute.networks',
        project=self.PROJECT_ID,
        network=kwargs.get('network'))
    subnetwork = resources.REGISTRY.Create(
        'compute.subnetworks',
        project=self.PROJECT_ID,
        region=self.REGION,
        subnetwork=kwargs.get('subnetwork'))
    return self.messages.UsableSubnetwork(
        subnetwork=subnetwork.RelativeName(),
        network=network.RelativeName(),
        ipCidrRange=kwargs.get('ipCidrRange'),
        secondaryIpRanges=kwargs.get('secondaryIpRanges', []),
        statusMessage=kwargs.get('statusMessage'))

  def _MakeListUsableSubnetworksResponse(self, subnets):
    return self.messages.ListUsableSubnetworksResponse(subnetworks=subnets)

  def _ExpectListUsableSubnets(self, response, exception=None):
    req = self.messages.ContainerProjectsAggregatedUsableSubnetworksListRequest(
        parent=self.PROJECT_REF.RelativeName(), pageSize=500, filter='')
    if exception:
      response = None
    self.mocked_client.projects_aggregated_usableSubnetworks.List.Expect(
        req, response=response, exception=exception)

  def ExpectUpdateNodePool(self,
                           node_pool_name,
                           workload_metadata_config=None,
                           locations=None,
                           response=None,
                           exception=None,
                           zone=None,
                           upgrade_settings=None):
    if not zone:
      zone = self.ZONE
    if locations is None:
      locations = []
    msg = self.messages.UpdateNodePoolRequest(
        name=api_adapter.ProjectLocationClusterNodePool(self.PROJECT_ID, zone,
                                                        self.CLUSTER_NAME,
                                                        node_pool_name),
        workloadMetadataConfig=workload_metadata_config,
        upgradeSettings=upgrade_settings,
        locations=locations)
    self.mocked_client.projects_locations_clusters_nodePools.Update.Expect(
        msg, response=response, exception=exception)


class AlphaTestBase(BetaTestBase):
  """Mixin class for testing v1alpha1."""
  API_VERSION = 'v1alpha1'

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _MakeCluster(self, **kwargs):
    cluster = super(AlphaTestBase, self)._MakeCluster(**kwargs)
    return cluster

  def _MakeNodePool(self, **kwargs):
    node_pool = BetaTestBase._MakeNodePool(self, **kwargs)
    if kwargs.get('localSsdVolumeConfigs') is not None:
      node_pool.config.localSsdVolumeConfigs = kwargs.get(
          'localSsdVolumeConfigs')
    node_pool.config.sandboxConfig = kwargs.get('sandboxConfig')
    node_pool.config.nodeGroup = kwargs.get('nodeGroup')
    node_pool.config.linuxNodeConfig = kwargs.get('linuxNodeConfig')
    node_pool.config.kubeletConfig = kwargs.get('kubeletConfig')

    return node_pool


class IntegrationTestBase(e2e_base.WithServiceAuth,
                          sdk_test_base.WithOutputCapture):
  """Base class for container integration tests."""

  REGION = 'us-central1'
  ZONE = 'us-central1-f'


class ClustersTestBase(UnitTestBase):
  """Base class for clusters command tests."""

  def SetUp(self):
    self.clusters_command_base = self.COMMAND_BASE + ' clusters --zone {0}'
    self.regional_clusters_command_base = (
        self.COMMAND_BASE + ' clusters --region {0}')
    kubeconfig_path = kconfig.Kubeconfig.DefaultPath()
    if os.path.exists(kubeconfig_path):
      os.unlink(kubeconfig_path)
    self.msgs = core_apis.GetMessagesModule('container', self.API_VERSION)
    self._PatchSDKBinPath()


class NodePoolsTestBase(UnitTestBase):
  """Base class for node-pools command tests."""

  def SetUp(self):
    self.node_pools_command_base = self.COMMAND_BASE + ' node-pools --zone {0}'
    self.regional_node_pools_command_base = (
        self.COMMAND_BASE + ' node-pools --region {0}')
    kubeconfig_path = kconfig.Kubeconfig.DefaultPath()
    if os.path.exists(kubeconfig_path):
      os.unlink(kubeconfig_path)
    self.msgs = core_apis.GetMessagesModule('container', self.API_VERSION)

  def HttpError(self):
    return http_error.MakeHttpError(
        400,
        'your request is bad and you should feel bad.',
        url='https://fake-url.io')


class OperationsTestBase(UnitTestBase):
  """Base class for operations command tests."""

  def SetUp(self):
    self.operations_command_base = self.COMMAND_BASE + ' operations'
    self.msgs = core_apis.GetMessagesModule('container', self.API_VERSION)


class GetServerConfigTestBase(UnitTestBase):
  """Base class for get-server-config command tests."""

  def SetUp(self):
    self.get_server_config_command_base = (
        self.COMMAND_BASE + ' get-server-config')
    self.msgs = core_apis.GetMessagesModule('container', self.API_VERSION)


class SubnetsTestBase(UnitTestBase):
  """Base class for subnets command tests."""

  def SetUp(self):
    self.SetEncoding('ascii')
    self.subnets_command_base = self.COMMAND_BASE + ' subnets'
    self.msgs = core_apis.GetMessagesModule('container', self.API_VERSION)
    status_enum = self.msgs.UsableSubnetworkSecondaryRange.StatusValueValuesEnum
    self.unused = status_enum.UNUSED
    self.in_use_service = status_enum.IN_USE_SERVICE
    self.in_use_shareable_pod = status_enum.IN_USE_SHAREABLE_POD
    self.in_use_managed_pod = status_enum.IN_USE_MANAGED_POD
