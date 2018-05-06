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

"""Tests for 'clusters create' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
import json
import os

from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import kubeconfig as kconfig
from googlecloudsdk.api_lib.container import util as c_util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import constants
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.container import base
from six.moves import range  # pylint: disable=redefined-builtin


class CreateTestGA(parameterized.TestCase, base.TestBaseV1, base.GATestBase,
                   base.ClustersTestBase):
  """gcloud GA track using container v1 API."""

  def SetUp(self):
    self.api_mismatch = False

  def updateResponse(self, cluster, **kwargs):
    """Update the CreateCluster response with fake values."""
    fake = {
        'ca_data': 'fakecertificateauthoritydata',
        'cert_data': 'fakeclientcertificatedata',
        'endpoint': self.ENDPOINT,
        'key_data': 'fakeclientkeydata',
        'status': self.running,
        'statusMessage': 'Running',
        'zone': self.ZONE,
    }
    cluster.update(fake)
    cluster.update(kwargs)

  # TODO(b/64575339) Make all these tests use this.
  def makeExpectedAndReturnClusters(self, cluster_kwargs):
    """Create mock cluster objects."""
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    return_kwargs = cluster_kwargs.copy()
    self.updateResponse(return_kwargs)
    return_cluster = self._MakeCluster(**return_kwargs)
    return expected_cluster, return_cluster

  def ExpectCreateCalls(self, location=None):
    if not location:
      location = self.ZONE
    kwargs = {'zone': location}
    # Create cluster returns operation pending
    self.ExpectCreateCluster(self._MakeCluster(),
                             self._MakeOperation(**kwargs),
                             zone=location)
    # Initial get operation returns pending
    self.ExpectGetOperation(self._MakeOperation(**kwargs))
    # Second get operation returns done
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done, **kwargs))
    # Get cluster returns valid cluster
    self.ExpectGetCluster(self._RunningCluster(**kwargs), zone=location)

  def _TestCreateDefaults(self, location):
    self.ExpectCreateCalls(location)
    self.assertIsNone(c_util.ClusterConfig.Load(
        self.CLUSTER_NAME, location, self.PROJECT_ID))
    # Set an initial current-context in kubeconfig to verify we overwrite it
    initial = kconfig.Kubeconfig.Default()
    initial.SetCurrentContext('current-context')
    initial.SaveToFile()
    if location == self.REGION:
      self.Run(
          self.regional_clusters_command_base.format(location) +
          ' create {0}'.format(self.CLUSTER_NAME))
    else:
      self.Run(
          self.clusters_command_base.format(location) +
          ' create {0}'.format(self.CLUSTER_NAME))
    kwargs = {'zone': location}
    cluster = self._RunningCluster(**kwargs)
    self.AssertOutputContains(str(cluster.status))
    self.AssertOutputContains(str(cluster.endpoint))
    if self.api_mismatch and location == self.REGION:
      self.AssertErrContains('You invoked')
    self.AssertErrContains('Created')
    c_config = c_util.ClusterConfig.Load(
        self.CLUSTER_NAME, location, self.PROJECT_ID)
    self._TestDefaultAuth(c_config)
    self.AssertErrContains(c_util.KUBECONFIG_USAGE_FMT.format(
        cluster=self.CLUSTER_NAME,
        context=c_config.kube_context))
    self.assertIsNone(properties.VALUES.container.cluster.Get())

  def testCreateDefaults(self):
    self.WriteInput('y')
    self._TestCreateDefaults(self.ZONE)

  def testCreateDefaultsRegional(self):
    self.WriteInput('y\ny')
    self._TestCreateDefaults(self.REGION)

  def testCreateDefaultsJsonOutput(self):
    self.ExpectCreateCalls()
    self.assertIsNone(c_util.ClusterConfig.Load(
        self.CLUSTER_NAME, self.ZONE, self.PROJECT_ID))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --format json'.format(self.CLUSTER_NAME))
    result = json.loads(self.GetOutput())
    json_cluster = result[0]
    self.assertEqual(json_cluster['status'], str(self.running))

  def testCreateAsync(self):
    # Create cluster returns operation pending
    self.ExpectCreateCluster(self._MakeCluster(), self._MakeOperation())
    # Get cluster returns pending cluster
    cluster = self._MakeCluster(
        status=self.provisioning,
        statusMessage='Provisioning',
        endpoint=None,
        zone=self.ZONE)
    self.ExpectGetCluster(cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --async'.format(self.CLUSTER_NAME))
    self.assertIsNone(c_util.ClusterConfig.Load(
        self.CLUSTER_NAME, self.ZONE, self.PROJECT_ID))
    self.AssertOutputContains(str(cluster.status))
    self.AssertErrNotContains('Created')
    self.AssertErrNotContains('kubeconfig')
    self.assertIsNone(properties.VALUES.container.cluster.Get())

  def testCreateNoDefaults(self):
    properties.VALUES.container.new_scopes_behavior.Set(True)
    cluster_kwargs = {
        'password':
            'secret',
        'username':
            'derpy',
        'name':
            'my-little-cluster-kubernetes-is-magic',
        'locations':
            sorted(['us-central1-a', 'us-central1-b', 'us-central1-f']),
        'machineType':
            'n1-standard-2',
        'clusterApiVersion':
            '1.7.1',
        'nodeVersion':
            '1.6.8',
        'network':
            'my-network',
        'subnetwork':
            'my-sub-network',
        'loggingService':
            'none',
        'monitoringService':
            'none',
        'diskSizeGb':
            2000,
        'diskType':
            'pd-ssd',
        'clusterIpv4Cidr':
            '10.11.240.0/20',
        'addonsConfig':
            self.msgs.AddonsConfig(
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=False),
                httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=True),
                kubernetesDashboard=self.msgs.KubernetesDashboard(
                    disabled=True),
                networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                    disabled=True)),
        'localSsdCount':
            2,
        'tags':
            sorted(['http-server', 'https-server']),
        'nodeLabels':
            self.msgs.NodeConfig.LabelsValue(
                additionalProperties=[
                    self.msgs.NodeConfig.LabelsValue.AdditionalProperty(
                        key='env', value='prod')
                ],),
        'nodeTaints': [
            self.msgs.NodeTaint(
                key='key1',
                value='val1',
                effect=self.msgs.NodeTaint.EffectValueValuesEnum.NO_SCHEDULE)
        ],
        'autoscaling':
            self.msgs.NodePoolAutoscaling(
                enabled=True, minNodeCount=1, maxNodeCount=5),
        'imageType':
            'custom',
        'nodeImageConfig':
            self.msgs.CustomImageConfig(
                image='cos-63',
                imageFamily='cos-cloud',
                imageProject='gke-node-images'),
        'preemptible':
            True,
        'management':
            self.msgs.NodeManagement(
                autoRepair=True, autoUpgrade=True, upgradeOptions=None),
        'authorizedNetworks':
            self.msgs.MasterAuthorizedNetworksConfig(
                enabled=True,
                cidrBlocks=[
                    self.msgs.CidrBlock(cidrBlock='10.0.0.1/32'),
                    self.msgs.CidrBlock(cidrBlock='10.0.0.2/32'),
                ],
            ),
        'legacyAbac':
            self.msgs.LegacyAbac(enabled=True),
        'oauthScopes': [
            'https://www.googleapis.com/auth/devstorage.read_only',
            'https://www.googleapis.com/auth/logging.write',
            'https://www.googleapis.com/auth/monitoring',
            'https://www.googleapis.com/auth/service.management.readonly',
            'https://www.googleapis.com/auth/servicecontrol',
            'https://www.googleapis.com/auth/trace.append',
        ],
    }
    cluster_kwargs['nodePools'] = [self._MakeDefaultNodePool(
        nodePoolName='default-pool-{pool}'.format(pool=pool_index),
        initialNodeCount=500 if pool_index < 3 else 499,
        **cluster_kwargs) for pool_index in range(4)]
    # Cluster create returns operation pending
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(targetLink=self.TARGET_LINK.format(
            self.API_VERSION,
            self.PROJECT_NUM,
            self.ZONE,
            cluster_kwargs['name'])))
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(
        status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs.copy()
    self.updateResponse(
        return_args,
        currentMasterVersion=cluster_kwargs['clusterApiVersion'],
        currentNodeCount=1999,
        currentNodeVersion=cluster_kwargs['clusterApiVersion'],
        imageType=cluster_kwargs['imageType'].upper())
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {name} --username={username} --password={password} '
        '--num-nodes=1999 --max-nodes-per-pool=500 '
        '--machine-type={machineType} '
        '--additional-zones us-central1-a,us-central1-b '
        '--disk-size=2000 '
        '--disk-type={diskType} '
        '--cluster-ipv4-cidr=10.11.240.0/20 '
        '--cluster-version={clusterApiVersion} '
        '--node-version={nodeVersion} '
        '--network={network} '
        '--subnetwork={subnetwork} '
        '--no-enable-cloud-logging '
        '--no-enable-cloud-monitoring '
        '--enable-legacy-authorization '
        '--addons=HorizontalPodAutoscaling '
        '--local-ssd-count={localSsdCount} '
        '--tags=http-server,https-server '
        '--node-labels=env=prod '
        '--node-taints=key1=val1:NoSchedule '
        '--enable-autoscaling '
        '--min-nodes=1 '
        '--max-nodes=5 '
        '--image-type={imageType} '
        '--image=cos-63 '
        '--image-family=cos-cloud '
        '--image-project=gke-node-images '
        '--preemptible '
        '--enable-autorepair '
        '--enable-autoupgrade '
        '--enable-master-authorized-networks '
        '--master-authorized-networks=10.0.0.1/32,10.0.0.2/32 '
        .format(**cluster_kwargs))
    self.AssertOutputMatches(
        (r'NAME LOCATION MASTER_VERSION MASTER_IP MACHINE_TYPE NODE_VERSION '
         'NUM_NODES STATUS\n'
         '{name} {zone} {version} {endpoint} {node_type} {node_version} '
         '{num_nodes} {status}\\n')
        .format(name=return_cluster.name,
                zone=return_cluster.zone,
                version=return_cluster.initialClusterVersion,
                endpoint=return_cluster.endpoint,
                node_type=return_cluster.nodePools[0].config.machineType,
                num_nodes=return_cluster.currentNodeCount,
                node_version=return_cluster.currentNodeVersion,
                status=return_cluster.status,),
        normalize_space=True)
    # Note: We use ErrContains rather than ErrEquals because this command can
    # have a warning at the top depending on if kubectl is currently available,
    # which can vary depending on environment.
    self.AssertErrContains("""This will enable the autorepair feature for \
nodes. Please see
https://cloud.google.com/kubernetes-engine/docs/node-auto-repair for more
information on node autorepairs.

This will enable the autoupgrade feature for nodes. Please see
https://cloud.google.com/kubernetes-engine/docs/node-management for more
information on node autoupgrades.

<START PROGRESS TRACKER>Creating cluster my-little-cluster-kubernetes-is-magic
<END PROGRESS TRACKER>SUCCESS
Created [https://container.googleapis.com/{0}/projects/fake-project-id/zones/us-central1-f/clusters/my-little-cluster-kubernetes-is-magic].
To inspect the contents of your cluster, go to: https://console.cloud.google.com/kubernetes/workload_/gcloud/us-central1-f/my-little-cluster-kubernetes-is-magic?project=fake-project-id
kubeconfig entry generated for my-little-cluster-kubernetes-is-magic.
""".format(self.API_VERSION))
    c_config = c_util.ClusterConfig.Load(
        cluster_kwargs['name'], self.ZONE, self.PROJECT_ID)
    self._TestDefaultAuth(c_config)

  def testCreateEnableAddons(self):
    cluster_kwargs = {
        'addonsConfig': self.msgs.AddonsConfig(
            httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=False),
            horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                disabled=True),
            kubernetesDashboard=self.msgs.KubernetesDashboard(
                disabled=False),
            networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                disabled=True)),
    }
    self.ExpectCreateCluster(self._MakeCluster(**cluster_kwargs),
                             self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.7.0'))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --addons=HttpLoadBalancing,KubernetesDashboard'
        .format(self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  @parameterized.parameters(('--service-account=my-sa --scopes=gke-default',
                             cli_test_base.MockArgumentError, 'At most one of'))
  def testNodeIdentityMutex(self, flags, expected_err, expected_msg):
    with self.AssertRaisesExceptionMatches(expected_err, expected_msg):
      self.Run('{base} create {name} --quiet {flags}'.format(
          base=self.clusters_command_base.format(self.ZONE),
          name=self.CLUSTER_NAME,
          flags=flags))

  def testServiceAccountCloudPlatformScopes(self):
    cluster_kwargs = {
        'serviceAccount': 'my-sa',
        'oauthScopes': ['https://www.googleapis.com/auth/cloud-platform',
                        'https://www.googleapis.com/auth/userinfo.email'],
    }
    expected_cluster, return_cluster = self.makeExpectedAndReturnClusters(
        cluster_kwargs)
    # Create cluster expects cluster and returns pending operation.
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    # Get operation returns done operation.
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns expected cluster, populated with other fields by server.
    self.ExpectGetCluster(return_cluster)
    self.Run('{base} create {name} '
             '--service-account=my-sa '
             '--quiet'.format(
                 base=self.clusters_command_base.format(self.ZONE),
                 name=self.CLUSTER_NAME))

  def _testScopes(self, flags, scopes):
    cluster_kwargs = {
        # Sort the scopes to assert equality of the lists
        'oauthScopes': sorted(scopes),
    }
    expected_cluster, return_cluster = self.makeExpectedAndReturnClusters(
        cluster_kwargs)
    # Create cluster expects cluster and returns pending operation.
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    # Get operation returns done operation.
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns expected cluster, populated with other fields by server.
    self.ExpectGetCluster(return_cluster)
    self.Run('{base} create {name} {flags} '
             '--quiet'.format(
                 base=self.clusters_command_base.format(self.ZONE),
                 name=self.CLUSTER_NAME,
                 flags=flags))

  def testCreateDefaultAuth(self):
    properties.VALUES.container.use_client_certificate.Set(None)
    properties.VALUES.container.use_app_default_credentials.Set(None)
    self.ExpectCreateCluster(self._MakeCluster(), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.3.0'))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0}'.format(self.CLUSTER_NAME))
    c_config = c_util.ClusterConfig.Load(
        self.CLUSTER_NAME, self.ZONE, self.PROJECT_ID)
    self._TestDefaultAuth(c_config)

  # TODO(b/70856999) Test creation with client cert auth.

  def testCreateADCAuth(self):
    properties.VALUES.container.use_app_default_credentials.Set(True)
    self.ExpectCreateCluster(self._MakeCluster(), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.3.0'))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0}'.format(self.CLUSTER_NAME))
    c_config = c_util.ClusterConfig.Load(
        self.CLUSTER_NAME, self.ZONE, self.PROJECT_ID)
    self.assertIsNotNone(c_config)
    self.assertIsNotNone(c_config.auth_provider)
    self.assertEqual(c_config.auth_provider.get('name'), 'gcp')
    self.assertTrue(c_config.has_ca_cert)
    self.assertIsNone(c_config.auth_provider.get('cmd-path'))

  def testCreateWarning(self):
    msg = 'Cluster was created but API is reporting 1 unhealthy node.'
    # Create cluster returns operation pending
    self.ExpectCreateCluster(self._MakeCluster(), self._MakeOperation())
    # Initial get operation returns pending
    self.ExpectGetOperation(self._MakeOperation())
    # Second get operation returns done with detail
    self.ExpectGetOperation(self._MakeOperation(
        status=self.op_done,
        detail=msg))
    # Get cluster returns valid cluster
    self.ExpectGetCluster(self._RunningCluster())
    self.assertIsNone(c_util.ClusterConfig.Load(
        self.CLUSTER_NAME, self.ZONE, self.PROJECT_ID))
    # Set an initial current-context in kubeconfig to verify we overwrite it
    initial = kconfig.Kubeconfig.Default()
    initial.SetCurrentContext('current-context')
    initial.SaveToFile()
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0}'.format(self.CLUSTER_NAME))
    cluster = self._RunningCluster()
    c_config = c_util.ClusterConfig.Load(
        self.CLUSTER_NAME, self.ZONE, self.PROJECT_ID)
    self._TestDefaultAuth(c_config)
    self.AssertOutputContains(str(cluster.status))
    self.AssertOutputContains(str(cluster.endpoint))
    self.AssertErrContains('Created')
    self.AssertErrContains(c_util.KUBECONFIG_USAGE_FMT.format(
        cluster=self.CLUSTER_NAME,
        context=c_config.kube_context))
    self.assertIsNone(properties.VALUES.container.cluster.Get())
    self.assertEqual(kconfig.Kubeconfig.Default().current_context,
                     c_config.kube_context)
    self.AssertErrContains(msg)

  def testCreateMissingEnv(self):
    # HOME is set to a tmp directory in UnitTestBase.
    # Temporarily unset HOME so we can verify expected warning.
    self.assertEqual(self.tmp_home.path, os.environ['HOME'])
    self.ExpectCreateCalls()
    self.StartDictPatch('os.environ',
                        {'HOME': '', 'HOMEDRIVE': '', 'HOMEPATH': '',
                         'USERPROFILE': ''})
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0}'.format(self.CLUSTER_NAME))
    self.AssertErrContains('KUBECONFIG must be set')

  def testCreateMissingZone(self):
    with self.assertRaises(exceptions.MinimumArgumentException):
      self.Run(self.COMMAND_BASE +
               ' clusters create {0}'.format(self.CLUSTER_NAME))

  def testCreateNegativeNodes(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' create {0} --num-nodes=-1'.format(self.CLUSTER_NAME))
    self.AssertErrContains('argument --num-nodes')

  def testCreateInvalidNodeLabels(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' create {0} --node-labels=test=a,b'.format(self.CLUSTER_NAME))
    self.AssertErrContains('argument --node-labels')

  def testCreateInvalidNodeTaints(self):
    with self.assertRaises(c_util.Error):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' create {0} --node-taints=test=ab'.format(self.CLUSTER_NAME))
    self.AssertErrContains('argument --node-taints')

  def testCreateInvalidNodeTaintEffect(self):
    with self.assertRaises(c_util.Error):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' create {0} --node-taints=test=ab:RandomEffect'
               .format(self.CLUSTER_NAME))
    self.AssertErrContains('argument --node-taints')

  def testCreateEmptyTags(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' create {0} --tags='.format(self.CLUSTER_NAME))
    self.AssertErrContains('argument --tags')

  def testCreateZeroNodes(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' create {0} --num-nodes=0'.format(self.CLUSTER_NAME))
    self.AssertErrContains('argument --num-nodes')

  def testCreateUnauthorized(self):
    self.ExpectCreateCluster(self._MakeCluster(),
                             exception=base.UNAUTHORIZED_ERROR)
    with self.assertRaises(exceptions.HttpException):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --async'.format(self.CLUSTER_NAME))
    self.AssertErrContains('code=403, message=unauthorized')

  def testCreateGetOperationUnauthorized(self):
    self.ExpectCreateCluster(self._MakeCluster(), self._MakeOperation())
    self.ExpectGetOperation(
        self._MakeOperation(), exception=base.UNAUTHORIZED_ERROR)
    with self.assertRaises(exceptions.HttpException):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0}'.format(self.CLUSTER_NAME))
    self.AssertErrContains('code=403, message=unauthorized')

  def testCreateMissingProject(self):
    properties.VALUES.core.project.Set(None)
    with self.assertRaises(properties.RequiredPropertyError):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0}'.format(self.CLUSTER_NAME))
    self.AssertErrContains(
        'The required property [project] is not currently set.')

  def testCreateMasterAuthorizedNetworksDisable(self):
    cluster_kwargs = {}
    # Cluster create returns operation pending
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation())
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--no-enable-master-authorized-networks'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testCreateInvalidMasterAuthorizedNetworksWithoutEnable(self):
    with self.assertRaises(c_util.Error):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' create {0} --master-authorized-networks=10.0.0.1/32'.format(
                   self.CLUSTER_NAME))
      self.AssertErrContains('Cannot use --master-authorized-networks')

  def testEnableIPAlias(self):
    cluster_kwargs = {}
    # Cluster create returns operation pending
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    policy = self._MakeIPAllocationPolicy(
        clusterIpv4Cidr=None,
        createSubnetwork=True,
        nodeIpv4Cidr='/24',
        servicesIpv4Cidr='10.0.0.0/16',
        subnetworkName='my-subnet',
        useIpAliases=True)
    expected_cluster.ipAllocationPolicy = policy
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs.copy()
    self.updateResponse(
        return_args, enableKubernetesAlpha=True, ipAllocationPolicy=policy)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-ip-alias '
        '--services-ipv4-cidr 10.0.0.0/16 '
        '--create-subnetwork name=my-subnet,range=/24 '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testEnableIPAliasBadArgs(self):
    base_command = (
        self.clusters_command_base.format(self.ZONE) +
        ' create {name} --quiet'.format(name=self.CLUSTER_NAME))
    for command, expected_err in [
        (base_command + ' --services-ipv4-cidr 10.0.0.0/16',
         api_adapter.PREREQUISITE_OPTION_ERROR_MSG.format(
             prerequisite='enable-ip-alias', opt='services-ipv4-cidr')),
        (base_command + ' --create-subnetwork name=foo',
         api_adapter.PREREQUISITE_OPTION_ERROR_MSG.format(
             prerequisite='enable-ip-alias', opt='create-subnetwork')),
        (base_command + ' --cluster-secondary-range-name=foo',
         api_adapter.PREREQUISITE_OPTION_ERROR_MSG.format(
             prerequisite='enable-ip-alias',
             opt='cluster-secondary-range-name')),
        (base_command + ' --services-secondary-range-name=foo',
         api_adapter.PREREQUISITE_OPTION_ERROR_MSG.format(
             prerequisite='enable-ip-alias',
             opt='services-secondary-range-name')),
        (base_command + ' --enable-ip-alias --create-subnetwork foo=foo',
         api_adapter.CREATE_SUBNETWORK_INVALID_KEY_ERROR_MSG.format(key='foo')),
        (base_command +
         ' --enable-ip-alias --subnetwork foo --create-subnetwork '
         'range=10.0.0.0/16',
         api_adapter.CREATE_SUBNETWORK_WITH_SUBNETWORK_ERROR_MSG),
    ]:
      self.AssertRaisesExceptionMatches(c_util.Error, expected_err, self.Run,
                                        command)

  @parameterized.parameters('', '--username=admin', '--enable-basic-auth')
  def testEnableBasicAuth(self, flags):
    cluster_kwargs = {}
    # Cluster create returns operation pending
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run('{base} create {name} {flags} '
             '--quiet'.format(
                 base=self.clusters_command_base.format(self.ZONE),
                 name=self.CLUSTER_NAME,
                 flags=flags))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  @parameterized.parameters('--username=""', '--no-enable-basic-auth')
  def testDisableBasicAuth(self, flags):
    cluster_kwargs = {}
    # Cluster create returns operation pending
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    expected_cluster.masterAuth.username = ''
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run('{base} create {name} {flags} '
             '--quiet'.format(
                 base=self.clusters_command_base.format(self.ZONE),
                 name=self.CLUSTER_NAME,
                 flags=flags))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  @parameterized.parameters(
      ('--username="" --enable-basic-auth', cli_test_base.MockArgumentError,
       'At most one of'),
      ('--username="" --no-enable-basic-auth', cli_test_base.MockArgumentError,
       'At most one of'),
      ('--username="u" --enable-basic-auth', cli_test_base.MockArgumentError,
       'At most one of'),
      ('--username="u" --no-enable-basic-auth', cli_test_base.MockArgumentError,
       'At most one of'),
      ('--username="" --password="mypass"', c_util.Error,
       constants.USERNAME_PASSWORD_ERROR_MSG),
      ('--no-enable-basic-auth --password="mypass"', c_util.Error,
       constants.USERNAME_PASSWORD_ERROR_MSG),
  )
  def testBasicAuthBadArgs(self, flags, expected_err, expected_msg):
    with self.AssertRaisesExceptionMatches(expected_err, expected_msg):
      self.Run('{base} create {name} --quiet {flags}'.format(
          base=self.clusters_command_base.format(self.ZONE),
          name=self.CLUSTER_NAME,
          flags=flags))

  @parameterized.parameters(
      ('--no-issue-client-certificate', False),
      ('--issue-client-certificate', True),
  )
  def testNoIssueClientCertificate(self, flags, expect_issue):
    cluster_kwargs = {}
    expected_cluster, return_cluster = self.makeExpectedAndReturnClusters(
        cluster_kwargs)
    (expected_cluster.masterAuth.clientCertificateConfig
     .issueClientCertificate) = expect_issue
    # Create cluster expects cluster and returns pending operation.
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    # Get operation returns done operation.
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns expected cluster, populated with other fields by server.
    self.ExpectGetCluster(return_cluster)
    self.Run('{base} create {name} {flags} '
             '--quiet'.format(
                 base=self.clusters_command_base.format(self.ZONE),
                 name=self.CLUSTER_NAME,
                 flags=flags))


class CreateTestGAOnly(CreateTestGA):
  """gcloud GA track only using container v1 API (not beta/alpha)."""

  @parameterized.parameters(
      ('--service-account=my-sa --enable-cloud-endpoints',
       cli_test_base.MockArgumentError, 'At most one of'),
      ('--service-account=my-sa --no-enable-cloud-endpoints',
       cli_test_base.MockArgumentError, 'At most one of'),
      ('--service-account=my-sa --scopes=gke-default --enable-cloud-endpoints',
       cli_test_base.MockArgumentError, 'At most one of'),
      ('--service-account=my-sa --scopes=gke-default '
       '--no-enable-cloud-endpoints', cli_test_base.MockArgumentError,
       'At most one of'))
  def testNodeIdentityMutex(self, flags, expected_err, expected_msg):
    with self.AssertRaisesExceptionMatches(expected_err, expected_msg):
      self.Run('{base} create {name} --quiet {flags}'.format(
          base=self.clusters_command_base.format(self.ZONE),
          name=self.CLUSTER_NAME,
          flags=flags))

  @parameterized.parameters(('--enable-cloud-endpoints', c_util.Error,
                             '--[no-]enable-cloud-endpoints is not allowed'),
                            ('--no-enable-cloud-endpoints', c_util.Error,
                             '--[no-]enable-cloud-endpoints is not allowed'))
  def testNoEnableCloudEndpointsNewScopesBehaviorMutex(
      self, flags, expected_err, expected_msg):
    properties.VALUES.container.new_scopes_behavior.Set(True)
    with self.AssertRaisesExceptionMatches(expected_err, expected_msg):
      self.Run('{base} create {name} --quiet {flags}'.format(
          base=self.clusters_command_base.format(self.ZONE),
          name=self.CLUSTER_NAME,
          flags=flags))

  @parameterized.named_parameters(
      ('Implicit default', '', [
          'gke-version-default',
          'https://www.googleapis.com/auth/devstorage.read_only',
          'https://www.googleapis.com/auth/logging.write',
          'https://www.googleapis.com/auth/monitoring',
          'https://www.googleapis.com/auth/service.management.readonly',
          'https://www.googleapis.com/auth/servicecontrol',
          'https://www.googleapis.com/auth/trace.append',
      ]),
      ('Explicit default', '--scopes=gke-default', [
          'gke-version-default',
          'https://www.googleapis.com/auth/devstorage.read_only',
          'https://www.googleapis.com/auth/logging.write',
          'https://www.googleapis.com/auth/monitoring',
          'https://www.googleapis.com/auth/service.management.readonly',
          'https://www.googleapis.com/auth/servicecontrol',
          'https://www.googleapis.com/auth/trace.append',
      ]),
      ('Explicit endpoints', '--scopes=service-management,service-control', [
          'gke-version-default',
          'https://www.googleapis.com/auth/service.management.readonly',
          'https://www.googleapis.com/auth/servicecontrol',
      ]),
      ('Explicit endpoints (not aliased)',
       '--scopes=https://www.googleapis.com/auth/service.management.readonly,'
       'https://www.googleapis.com/auth/servicecontrol', [
           'gke-version-default',
           'https://www.googleapis.com/auth/service.management.readonly',
           'https://www.googleapis.com/auth/servicecontrol',
       ]),
      # Even though these use --no-enable-cloud-endpoints, the user already gets
      # a deprecation warning for the flag, so don't worry about printing more
      # info about how it interacts with scopes.
      ('Implicit default with --no-enable-cloud-endpoints',
       '--no-enable-cloud-endpoints', [
           'gke-version-default',
           'https://www.googleapis.com/auth/devstorage.read_only',
           'https://www.googleapis.com/auth/logging.write',
           'https://www.googleapis.com/auth/monitoring',
           'https://www.googleapis.com/auth/trace.append',
       ]),
      ('Explicit default with --no-enable-cloud-endpoints',
       '--scopes=gke-default --no-enable-cloud-endpoints', [
           'gke-version-default',
           'https://www.googleapis.com/auth/devstorage.read_only',
           'https://www.googleapis.com/auth/logging.write',
           'https://www.googleapis.com/auth/monitoring',
           'https://www.googleapis.com/auth/trace.append',
       ]),
      ('Explicit endpoints with --no-enable-cloud-endpoints',
       '--scopes=service-management,service-control '
       '--no-enable-cloud-endpoints', [
           'gke-version-default',
       ]),
      ('Explicit endpoints (not aliased) with --no-enable-cloud-endpoints',
       '--scopes=https://www.googleapis.com/auth/service.management.readonly,'
       'https://www.googleapis.com/auth/servicecontrol '
       '--no-enable-cloud-endpoints', [
           'gke-version-default',
       ]),
      ('Other scopes with --no-enable-cloud-endpoints',
       '--scopes=storage-ro,pubsub --no-enable-cloud-endpoints', [
           'gke-version-default',
           'https://www.googleapis.com/auth/devstorage.read_only',
           'https://www.googleapis.com/auth/pubsub'
       ]),
      ('Unrecognized with --no-enable-cloud-endpoints',
       '--scopes=idontrecognizethisscopebutgoforit --no-enable-cloud-endpoints',
       [
           'gke-version-default',
           'idontrecognizethisscopebutgoforit',
       ]),
      ('Empty with --no-enable-cloud-endpoints',
       '--scopes="" --no-enable-cloud-endpoints', [
           'gke-version-default',
       ]),
  )
  def testScopesComputeWarning(self, flags, scopes):
    self._testScopes(flags, scopes)
    self.AssertErrContains('new clusters will no longer get compute-rw')
    self.AssertErrNotContains('The behavior of --scopes will change')

  @parameterized.named_parameters(
      ('Other scopes', '--scopes=storage-ro,pubsub', [
          'gke-version-default',
          'https://www.googleapis.com/auth/devstorage.read_only',
          'https://www.googleapis.com/auth/pubsub',
          'https://www.googleapis.com/auth/service.management.readonly',
          'https://www.googleapis.com/auth/servicecontrol',
      ]),
      ('Unrecognized', '--scopes=idontrecognizethisscopebutgoforit ', [
          'gke-version-default',
          'idontrecognizethisscopebutgoforit',
          'https://www.googleapis.com/auth/service.management.readonly',
          'https://www.googleapis.com/auth/servicecontrol',
      ]),
      ('Empty', '--scopes=""', [
          'gke-version-default',
          'https://www.googleapis.com/auth/service.management.readonly',
          'https://www.googleapis.com/auth/servicecontrol',
      ]),
  )
  def testScopesBothWarnings(self, flags, scopes):
    self._testScopes(flags, scopes)
    self.AssertErrContains('new clusters will no longer get compute-rw')
    self.AssertErrContains('The behavior of --scopes will change')

  @parameterized.named_parameters(
      ("Warn because had to add endpoints scopes, even though didn't have to "
       'add compute-rw or storage-ro', '--scopes=compute-rw,storage-ro', [
           'https://www.googleapis.com/auth/compute',
           'https://www.googleapis.com/auth/devstorage.read_only',
           'https://www.googleapis.com/auth/service.management.readonly',
           'https://www.googleapis.com/auth/servicecontrol',
       ]),)
  def testScopesEndpointsWarning(self, flags, scopes):
    self._testScopes(flags, scopes)
    self.AssertErrNotContains('new clusters will no longer get compute-rw')
    self.AssertErrContains('The behavior of --scopes will change')

  @parameterized.named_parameters(
      ('Implicit default with new_scopes_behavior=True', '', [
          'https://www.googleapis.com/auth/devstorage.read_only',
          'https://www.googleapis.com/auth/logging.write',
          'https://www.googleapis.com/auth/monitoring',
          'https://www.googleapis.com/auth/service.management.readonly',
          'https://www.googleapis.com/auth/servicecontrol',
          'https://www.googleapis.com/auth/trace.append',
      ]), ('Explicit default with new_scopes_behavior=True',
           '--scopes=gke-default', [
               'https://www.googleapis.com/auth/devstorage.read_only',
               'https://www.googleapis.com/auth/logging.write',
               'https://www.googleapis.com/auth/monitoring',
               'https://www.googleapis.com/auth/service.management.readonly',
               'https://www.googleapis.com/auth/servicecontrol',
               'https://www.googleapis.com/auth/trace.append',
           ]),
      ('Explicit endpoints with new_scopes_behavior=True',
       '--scopes=service-management,service-control', [
           'https://www.googleapis.com/auth/service.management.readonly',
           'https://www.googleapis.com/auth/servicecontrol',
       ]),
      ('Explicit endpoints (not aliased) with new_scopes_behavior=True',
       '--scopes=https://www.googleapis.com/auth/service.management.readonly,'
       'https://www.googleapis.com/auth/servicecontrol', [
           'https://www.googleapis.com/auth/service.management.readonly',
           'https://www.googleapis.com/auth/servicecontrol',
       ]), ('Other scopes with new_scopes_behavior=True',
            '--scopes=storage-ro,pubsub', [
                'https://www.googleapis.com/auth/devstorage.read_only',
                'https://www.googleapis.com/auth/pubsub'
            ]), ('Unrecognized with new_scopes_behavior=True',
                 '--scopes=idontrecognizethisscopebutgoforit', [
                     'idontrecognizethisscopebutgoforit',
                 ]), ('Empty with new_scopes_behavior=True', '--scopes=""', []))
  def testScopesNoWarningNewScopesBehavior(self, flags, scopes):
    properties.VALUES.container.new_scopes_behavior.Set(True)
    self._testScopes(flags, scopes)
    self.AssertErrNotContains('new clusters will no longer get compute-rw')
    self.AssertErrNotContains('The behavior of --scopes will change')

  @parameterized.named_parameters(
      ('Explicit default with compute-rw', '--scopes=gke-default,compute-rw', [
          'https://www.googleapis.com/auth/compute',
          'https://www.googleapis.com/auth/devstorage.read_only',
          'https://www.googleapis.com/auth/logging.write',
          'https://www.googleapis.com/auth/monitoring',
          'https://www.googleapis.com/auth/service.management.readonly',
          'https://www.googleapis.com/auth/servicecontrol',
          'https://www.googleapis.com/auth/trace.append',
      ]),
      ('Explicit endpoints, compute-rw, storage-ro',
       '--scopes=service-management,service-control,compute-rw,storage-ro', [
           'https://www.googleapis.com/auth/compute',
           'https://www.googleapis.com/auth/devstorage.read_only',
           'https://www.googleapis.com/auth/service.management.readonly',
           'https://www.googleapis.com/auth/servicecontrol',
       ]),
      ('Explicit endpoints, compute-rw, storage-ro (not aliased)',
       '--scopes=https://www.googleapis.com/auth/service.management.readonly,'
       'https://www.googleapis.com/auth/servicecontrol,'
       'https://www.googleapis.com/auth/compute,'
       'https://www.googleapis.com/auth/devstorage.read_only', [
           'https://www.googleapis.com/auth/compute',
           'https://www.googleapis.com/auth/devstorage.read_only',
           'https://www.googleapis.com/auth/service.management.readonly',
           'https://www.googleapis.com/auth/servicecontrol',
       ]),
      ("Don't warn because used --no-enable-cloud-endpoints, so will already "
       'get a deprecation warning for that.',
       '--scopes=compute-rw,gke-default --no-enable-cloud-endpoints', [
           'https://www.googleapis.com/auth/compute',
           'https://www.googleapis.com/auth/devstorage.read_only',
           'https://www.googleapis.com/auth/logging.write',
           'https://www.googleapis.com/auth/monitoring',
           'https://www.googleapis.com/auth/trace.append',
       ]),
  )
  def testScopesNoWarningEdgeCases(self, flags, scopes):
    self._testScopes(flags, scopes)
    self.AssertErrNotContains('new clusters will no longer get compute-rw')
    self.AssertErrNotContains('The behavior of --scopes will change')


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class CreateTestBetaV1API(base.BetaTestBase, CreateTestGA):
  """gcloud Beta track using container v1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(True)
    self.api_mismatch = True

  def testCreateAlphaCluster(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')
    cluster_kwargs = {'enableKubernetesAlpha': True}
    self.ExpectCreateCluster(self._MakeCluster(**cluster_kwargs),
                             self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    return_args.update({
        'expireTime': base.format_date_time('P30D'),
    })
    self.ExpectGetCluster(self._RunningClusterForVersion(
        '1.3.6', **cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --enable-kubernetes-alpha'.format(self.CLUSTER_NAME))
    c_config = c_util.ClusterConfig.Load(
        self.CLUSTER_NAME, self.ZONE, self.PROJECT_ID)
    self._TestDefaultAuth(c_config)
    self.AssertErrContains('Created')
    self.AssertErrContains(constants.KUBERNETES_ALPHA_PROMPT)

  def testCreateWithLabels(self):
    cluster_kwargs = {
        'labels': self.msgs.Cluster.ResourceLabelsValue(
            additionalProperties=[
                self.msgs.Cluster.ResourceLabelsValue.AdditionalProperty(
                    key='k', value='v'),
                self.msgs.Cluster.ResourceLabelsValue.AdditionalProperty(
                    key='k2', value=''),
            ],
        ),
    }

    # Cluster create returns operation pending
    self.ExpectCreateCluster(self._MakeCluster(**cluster_kwargs),
                             self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs.copy()
    self.updateResponse(
        return_args, clusterApiVersion='0.18.2', currentMasterVersion1='0.18.2')
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --labels=k=v,k2='.format(self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testCreateWithNodeTaints(self):
    effect_enum = self.msgs.NodeTaint.EffectValueValuesEnum
    taints = [
        self.msgs.NodeTaint(
            key='key1',
            value='val1',
            effect=effect_enum.NO_SCHEDULE),
        self.msgs.NodeTaint(
            key='key2',
            value='val2',
            effect=effect_enum.PREFER_NO_SCHEDULE),
        self.msgs.NodeTaint(
            key='key3',
            value='val3',
            effect=effect_enum.NO_EXECUTE)
    ]
    cluster_kwargs = {'nodeTaints': taints}

    # Cluster create returns operation pending
    self.ExpectCreateCluster(self._MakeCluster(**cluster_kwargs),
                             self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs.copy()
    self.updateResponse(
        return_args, clusterApiVersion='0.18.2', currentMasterVersion1='0.18.2')
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --node-taints='
        'key1=val1:NoSchedule,key2=val2:PreferNoSchedule,key3=val3:NoExecute'
        .format(self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testCreateMinCpuPlatform(self):
    cluster_kwargs = {'minCpuPlatform': 'Skylake'}
    self.ExpectCreateCluster(self._MakeCluster(**cluster_kwargs),
                             self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.3.0'))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --min-cpu-platform=Skylake'.format(self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testCreateMaintenanceWindow(self):
    m = self.messages
    cluster_kwargs = {
        'name': 'mw-cluster',
        'maintenancePolicy': m.MaintenancePolicy(
            window=m.MaintenanceWindow(
                dailyMaintenanceWindow=m.DailyMaintenanceWindow(
                    startTime='11:43'))),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(targetLink=self.TARGET_LINK.format(
            self.API_VERSION,
            self.PROJECT_NUM,
            self.ZONE,
            cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(
        status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create mw-cluster --maintenance-window=11:43')

  def testCreateEmptyMaintenanceWindow(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --maintenance-window: expected one argument'):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' create {0} --maintenance-window'.format(
                   self.CLUSTER_NAME))

  def testCreateInvalidMaintenanceWindow(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' create {0} --maintenance-window=24:93'.format(
                   self.CLUSTER_NAME))
    self.AssertErrContains('argument --maintenance-window')

  @parameterized.parameters(
      '--enable-cloud-endpoints',
      '--no-enable-cloud-endpoints',
  )
  def testEnableCloudEndpointsRemoved(self, flags):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'Flag --[no-]enable-cloud-endpoints has been removed'):
      self.Run('{base} create {name} --quiet {flags}'.format(
          base=self.clusters_command_base.format(self.ZONE),
          name=self.CLUSTER_NAME,
          flags=flags))

  @parameterized.named_parameters(
      ('Implicit default', '', [
          'https://www.googleapis.com/auth/devstorage.read_only',
          'https://www.googleapis.com/auth/logging.write',
          'https://www.googleapis.com/auth/monitoring',
          'https://www.googleapis.com/auth/service.management.readonly',
          'https://www.googleapis.com/auth/servicecontrol',
          'https://www.googleapis.com/auth/trace.append',
      ]),
      ('Explicit default', '--scopes=gke-default', [
          'https://www.googleapis.com/auth/devstorage.read_only',
          'https://www.googleapis.com/auth/logging.write',
          'https://www.googleapis.com/auth/monitoring',
          'https://www.googleapis.com/auth/service.management.readonly',
          'https://www.googleapis.com/auth/servicecontrol',
          'https://www.googleapis.com/auth/trace.append',
      ]),
      ('Other scopes', '--scopes=storage-ro,pubsub', [
          'https://www.googleapis.com/auth/devstorage.read_only',
          'https://www.googleapis.com/auth/pubsub',
      ]),
      ('Unrecognized', '--scopes=idontrecognizethisscopebutgoforit ', [
          'idontrecognizethisscopebutgoforit',
      ]),
      ('Empty', '--scopes=""', []),
  )
  def testScopes(self, flags, scopes):
    self._testScopes(flags, scopes)


# Mixin class must come in first to have the correct multi-inheritance behavior.
class CreateTestBetaV1Beta1API(base.TestBaseV1Beta1, CreateTestBetaV1API):
  """gcloud Beta track using container v1beta1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(False)
    self.api_mismatch = False

  def testCreateBetaFeatures(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'my-cluster',
        'workloadMetadataConfig':
            m.WorkloadMetadataConfig(nodeMetadata=m.WorkloadMetadataConfig.
                                     NodeMetadataValueValuesEnum.SECURE),
    }
    cluster_kwargs['nodePools'] = [
        self._MakeDefaultNodePool(
            nodePoolName='default-pool', initialNodeCount=500,
            **cluster_kwargs),
    ]
    # Cluster create returns operation pending.
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(
                self.API_VERSION, self.PROJECT_NUM, self.ZONE, cluster_kwargs[
                    'name'])))
    # Get operation returns done.
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster.
    return_args = cluster_kwargs.copy()
    return_args.update({
        'currentNodeCount': 500,
        'status': self.running,
        'endpoint': self.ENDPOINT,
        'statusMessage': 'Running',
        'zone': self.ZONE,
    })
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create my-cluster --num-nodes=500 '
        '--workload-metadata-from-node=secure')
    self.AssertOutputMatches(
        (r'NAME LOCATION MASTER_VERSION MASTER_IP MACHINE_TYPE NODE_VERSION '
         'NUM_NODES STATUS\n'
         '{name} {zone} {endpoint} '
         '{num_nodes} {status}\\n').format(
             name=return_cluster.name,
             num_nodes=return_cluster.currentNodeCount,
             zone=return_cluster.zone,
             endpoint=return_cluster.endpoint,
             status=return_cluster.status),
        normalize_space=True)

  def testCreateNodeLocations(self):
    locations = sorted(['us-central1-a', 'us-central1-b', self.ZONE])
    kwargs = {'name': self.CLUSTER_NAME, 'locations': locations}
    # Cluster create returns operation pending
    self.ExpectCreateCluster(
        self._MakeCluster(**kwargs),
        self._MakeOperation(targetLink=self.TARGET_LINK.format(
            self.API_VERSION, self.PROJECT_NUM, self.ZONE, kwargs['name'])))
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    self.ExpectGetCluster(self._RunningCluster(**kwargs))
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                  self.PROJECT_ID))
    # Set an initial current-context in kubeconfig to verify we overwrite it
    initial = kconfig.Kubeconfig.Default()
    initial.SetCurrentContext('current-context')
    initial.SaveToFile()
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --node-locations={1}'.format(self.CLUSTER_NAME, ','.join(
            locations)))

  def testEnablePodSecurityPolicy(self):
    psp_config = self.messages.PodSecurityPolicyConfig(enabled=True)
    cluster_kwargs = {
        'podSecurityPolicyConfig': psp_config
    }
    # Cluster create returns operation pending
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    expected_cluster.podSecurityPolicyConfig = psp_config
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run('{base} create {name} '
             '--enable-pod-security-policy'.format(
                 base=self.clusters_command_base.format(self.ZONE),
                 name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testCreateAllowRouteOverlap(self):
    cluster_kwargs = {'clusterIpv4Cidr': '10.1.0.0/16'}
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    policy = self._MakeIPAllocationPolicy(allowRouteOverlap=True)
    expected_cluster.ipAllocationPolicy = policy
    # Cluster create returns operation pending
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--allow-route-overlap --cluster-ipv4-cidr=10.1.0.0/16'.format(
            name=self.CLUSTER_NAME))

  def testCreateAllowRouteOverlapWithIPAlias(self):
    expected_cluster = self._MakeCluster()
    policy = self._MakeIPAllocationPolicy(
        allowRouteOverlap=True,
        useIpAliases=True,
        createSubnetwork=False,
        clusterIpv4Cidr='10.1.0.0/16',
        servicesIpv4Cidr='10.2.0.0/16')
    expected_cluster.ipAllocationPolicy = policy
    # Cluster create returns operation pending
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    self.ExpectGetCluster(self._RunningCluster())
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--allow-route-overlap --enable-ip-alias '
        '--cluster-ipv4-cidr=10.1.0.0/16 '
        '--services-ipv4-cidr=10.2.0.0/16'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  @parameterized.parameters(
      ('--allow-route-overlap',
       api_adapter.ALLOW_ROUTE_OVERLAP_WITHOUT_CLUSTER_CIDR_ERROR_MSG),
      ('--allow-route-overlap '
       '--enable-ip-alias',
       api_adapter.ALLOW_ROUTE_OVERLAP_WITHOUT_CLUSTER_CIDR_ERROR_MSG),
      ('--allow-route-overlap '
       '--enable-ip-alias '
       '--services-ipv4-cidr=10.1.0.0/16',
       api_adapter.ALLOW_ROUTE_OVERLAP_WITHOUT_CLUSTER_CIDR_ERROR_MSG),
      ('--allow-route-overlap '
       '--enable-ip-alias '
       '--cluster-ipv4-cidr=10.1.0.0/16',
       api_adapter.ALLOW_ROUTE_OVERLAP_WITHOUT_SERVICES_CIDR_ERROR_MSG),
  )
  def testCreateAllowRouteOverlapBadArgs(self, flags, expected_msg):
    command = (
        self.clusters_command_base.format(self.ZONE) +
        ' create {name} --quiet '.format(name=self.CLUSTER_NAME) + flags)
    self.AssertRaisesExceptionMatches(c_util.Error, expected_msg, self.Run,
                                      command)

  def testEnablePrivateCluster(self):
    cluster_kwargs = {
        'name': self.CLUSTER_NAME,
    }

    expected_cluster = self._MakeCluster(**cluster_kwargs)
    expected_cluster.privateCluster = True
    expected_cluster.masterIpv4CidrBlock = '172.16.10.0/28'
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)

    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--private-cluster '
        '--master-ipv4-cidr=172.16.10.0/28 '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')


# Mixin class must come in first to have the correct multi-inheritance behavior.
class CreateTestAlphaV1API(base.AlphaTestBase, CreateTestBetaV1API):
  """gcloud Alpha track using container v1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(True)
    self.api_mismatch = True

  def testCreateInvalidAcceleratorMissingType(self):
    properties.VALUES.core.disable_prompts.Set(False)
    with self.AssertRaisesArgumentErrorMatches(
        r'argument --accelerator: Key [type] required in dict arg but not '
        r'provided'):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' create {0} --accelerator=count=2'.format(self.CLUSTER_NAME))

  def testCreateWithValidAccelerators(self):
    m = self.messages
    cluster_kwargs = {
        'name': 'my-gpu-cluster',
        'accelerators': [
            m.AcceleratorConfig(acceleratorType='nvidia-tesla-k80',
                                acceleratorCount=int(2))
        ],
    }
    cluster_kwargs['nodePools'] = [self._MakeDefaultNodePool(
        nodePoolName='default-pool',
        initialNodeCount=500, **cluster_kwargs)]
    # Cluster create returns operation pending
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(targetLink=self.TARGET_LINK.format(
            self.API_VERSION,
            self.PROJECT_NUM,
            self.ZONE,
            cluster_kwargs['name'])))
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(
        status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs.copy()
    return_args.update({
        'currentNodeCount': 500,
        'status': self.running,
        'endpoint': self.ENDPOINT,
        'statusMessage': 'Running',
        'zone': self.ZONE,
    })
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create my-gpu-cluster --num-nodes=500 '
        '--accelerator=type=nvidia-tesla-k80,count=2')
    self.AssertOutputMatches(
        (r'NAME LOCATION MASTER_VERSION MASTER_IP MACHINE_TYPE NODE_VERSION '
         'NUM_NODES STATUS\n'
         '{name} {zone} {endpoint} '
         '{num_nodes} {status}\\n')
        .format(name=return_cluster.name,
                num_nodes=return_cluster.currentNodeCount,
                zone=return_cluster.zone,
                endpoint=return_cluster.endpoint,
                status=return_cluster.status,),
        normalize_space=True)

  def testAcceleratorCountDefaulting(self):
    m = self.messages
    cluster_kwargs = {
        'name': 'my-gpu-cluster',
        'accelerators': [
            m.AcceleratorConfig(acceleratorType='nvidia-tesla-k80',
                                acceleratorCount=int(1))
        ],
    }
    cluster_kwargs['nodePools'] = [self._MakeDefaultNodePool(
        nodePoolName='default-pool',
        initialNodeCount=500, **cluster_kwargs)]
    # Cluster create returns operation pending
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(targetLink=self.TARGET_LINK.format(
            self.API_VERSION,
            self.PROJECT_NUM,
            self.ZONE,
            cluster_kwargs['name'])))
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs.copy()
    return_args.update({
        'currentNodeCount': 500,
        'status': self.running,
        'endpoint': self.ENDPOINT,
        'statusMessage': 'Running',
        'zone': self.ZONE,
    })
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create my-gpu-cluster --num-nodes=500 '
        '--accelerator=type=nvidia-tesla-k80')
    self.AssertOutputMatches(
        (r'NAME LOCATION MASTER_VERSION MASTER_IP MACHINE_TYPE NODE_VERSION '
         'NUM_NODES STATUS\n'
         '{name} {zone} {endpoint} '
         '{num_nodes} {status}\\n')
        .format(name=return_cluster.name,
                num_nodes=return_cluster.currentNodeCount,
                zone=return_cluster.zone,
                endpoint=return_cluster.endpoint,
                status=return_cluster.status,),
        normalize_space=True)

  def testCreateMaintenanceWindow(self):
    m = self.messages
    cluster_kwargs = {
        'name': 'mw-cluster',
        'maintenancePolicy': m.MaintenancePolicy(
            window=m.MaintenanceWindow(
                dailyMaintenanceWindow=m.DailyMaintenanceWindow(
                    startTime='11:43'))),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(targetLink=self.TARGET_LINK.format(
            self.API_VERSION,
            self.PROJECT_NUM,
            self.ZONE,
            cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(
        status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create mw-cluster --maintenance-window=11:43')

  def testCreateEmptyMaintenanceWindow(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --maintenance-window: expected one argument'):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' create {0} --maintenance-window'.format(
                   self.CLUSTER_NAME))

  def testCreateInvalidMaintenanceWindow(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --maintenance-window: Bad value [24:93]: Maintenance '
        'windows must be passed in using HH:MM format.'):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' create {0} --maintenance-window=24:93'.format(
                   self.CLUSTER_NAME))


# Mixin class must come in first to have the correct multi-inheritance behavior.
class CreateTestAlphaV1Alpha1API(base.TestBaseV1Alpha1, CreateTestAlphaV1API,
                                 CreateTestBetaV1Beta1API):
  """gcloud Alpha track using container v1alpha1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(False)
    self.api_mismatch = False

  def testCreateAlphaFeatures(self):
    m = self.messages
    format_enum = self.messages.LocalSsdVolumeConfig.FormatValueValuesEnum
    cluster_kwargs = {
        'name':
            'my-cluster',
        'binaryAuthorization':
            m.BinaryAuthorization(enabled=True),
        'workloadMetadataConfig':
            m.WorkloadMetadataConfig(nodeMetadata=m.WorkloadMetadataConfig.
                                     NodeMetadataValueValuesEnum.SECURE),
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                resourceLimits=[
                    m.ResourceLimit(name='cpu',
                                    maximum=10),
                    m.ResourceLimit(name='memory',
                                    maximum=64,
                                    minimum=8),
                    m.ResourceLimit(name='nvidia-tesla-k80',
                                    maximum=4,
                                    minimum=1),
                ]),
        'localSsdVolumeConfigs': [
            m.LocalSsdVolumeConfig(count=2, type='nvme',
                                   format=format_enum.FS),
            m.LocalSsdVolumeConfig(count=1, type='scsi',
                                   format=format_enum.BLOCK),
        ],
    }
    cluster_kwargs['nodePools'] = [self._MakeDefaultNodePool(
        nodePoolName='default-pool',
        initialNodeCount=500, **cluster_kwargs)]
    # Cluster create returns operation pending
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(targetLink=self.TARGET_LINK.format(
            self.API_VERSION,
            self.PROJECT_NUM,
            self.ZONE,
            cluster_kwargs['name'])))
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(
        status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs.copy()
    return_args.update({
        'currentNodeCount': 500,
        'status': self.running,
        'endpoint': self.ENDPOINT,
        'statusMessage': 'Running',
        'zone': self.ZONE,
    })
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create my-cluster --num-nodes=500 '
        '--enable-binauthz '
        '--workload-metadata-from-node=secure '
        '--local-ssd-volumes count=2,type=nvme,format=fs '
        '--local-ssd-volumes count=1,type=scsi,format=block '
        '--enable-autoprovisioning --max-cpu 10 --max-memory 64 --min-memory 8 '
        '--max-accelerator type=nvidia-tesla-k80,count=4 '
        '--min-accelerator type=nvidia-tesla-k80,count=1 ')
    self.AssertOutputMatches(
        (r'NAME LOCATION MASTER_VERSION MASTER_IP MACHINE_TYPE NODE_VERSION '
         'NUM_NODES STATUS\n'
         '{name} {zone} {endpoint} '
         '{num_nodes} {status}\\n')
        .format(name=return_cluster.name,
                num_nodes=return_cluster.currentNodeCount,
                zone=return_cluster.zone,
                endpoint=return_cluster.endpoint,
                status=return_cluster.status,),
        normalize_space=True)

  def testCreateShowsChargesWarning(self):
    with self.assertRaises(console_io.UnattendedPromptError):
      self.Run(
          self.regional_clusters_command_base.format(self.REGION) +
          ' create {0}'.format(self.CLUSTER_NAME))
    self.AssertErrContains('in the future you may be charged for it')

  def testEnableSharedNetwork(self):
    cluster_kwargs = {
        'name': self.CLUSTER_NAME,
        'subnetwork': 'my-subnetwork',
    }

    policy = self._MakeIPAllocationPolicy(
        useIpAliases=True,
        createSubnetwork=False,
        servicesSecondaryRangeName='services-range',
        clusterSecondaryRangeName='cluster-range',
    )
    nc = self._MakeNetworkConfig(enableSharedNetwork=True)

    expected_cluster = self._MakeCluster(**cluster_kwargs)
    expected_cluster.ipAllocationPolicy = policy
    expected_cluster.enableKubernetesAlpha = True
    expected_cluster.networkConfig = nc
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(
        return_args,
        enableKubernetesAlpha=True,
        ipAllocationPolicy=policy,
        enableSharedNetwork=True,
        subnetwork=cluster_kwargs['subnetwork'])
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)

    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-shared-network '
        '--enable-kubernetes-alpha '
        '--enable-ip-alias '
        '--subnetwork my-subnetwork '
        '--cluster-secondary-range-name cluster-range '
        '--services-secondary-range-name services-range '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testEnableSharedNetworkBadArgs(self):
    base_command = (
        self.clusters_command_base.format(self.ZONE) + ' create {name} --quiet '
        '--enable-shared-network '.format(name=self.CLUSTER_NAME))
    subnetwork = '--subnetwork asub '
    alpha = '--enable-kubernetes-alpha '
    ip_alias = '--enable-ip-alias '
    cluster_range = '--cluster-secondary-range-name aclu'

    for command, expected_opt_err in [
        (base_command, 'enable-kubernetes-alpha'),
        (base_command + alpha, 'enable-ip-alias'),
        (base_command + alpha + ip_alias, 'subnetwork'),
        (base_command + alpha + ip_alias + subnetwork,
         'cluster-secondary-range-name'),
        (base_command + alpha + ip_alias + subnetwork + cluster_range,
         'services-secondary-range-name'),
    ]:
      self.AssertRaisesExceptionMatches(
          c_util.MissingArgForSharedSubnetError,
          c_util.ENABLE_SHARED_NETWORK_REQS_ERROR_MSG.format(expected_opt_err),
          self.Run, command)

  def testCreateMaintenanceWindow(self):
    m = self.messages
    cluster_kwargs = {
        'name': 'mw-cluster',
        'maintenancePolicy': m.MaintenancePolicy(
            window=m.MaintenanceWindow(
                dailyMaintenanceWindow=m.DailyMaintenanceWindow(
                    startTime='11:43'))),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(targetLink=self.TARGET_LINK.format(
            self.API_VERSION,
            self.PROJECT_NUM,
            self.ZONE,
            cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(
        status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create mw-cluster --maintenance-window=11:43')

  def testCreateResourceLimits(self):
    m = self.messages
    cluster_kwargs = {
        'name': 'rl-cluster',
        'clusterAutoscaling': m.ClusterAutoscaling(
            enableNodeAutoprovisioning=False,
            resourceLimits=[
                m.ResourceLimit(name='cpu', minimum=10, maximum=20),
                m.ResourceLimit(name='memory', minimum=16, maximum=128)
            ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(targetLink=self.TARGET_LINK.format(
            self.API_VERSION,
            self.PROJECT_NUM,
            self.ZONE,
            cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--no-enable-autoprovisioning --min-cpu 10 --max-cpu 20 '
        '--min-memory 16 --max-memory 128')

  def testCreateEmptyMaintenanceWindow(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' create {0} --maintenance-window'.format(
                   self.CLUSTER_NAME))
    self.AssertErrContains('argument --maintenance-window')

  def testCreateInvalidMaintenanceWindow(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' create {0} --maintenance-window=24:93'.format(
                   self.CLUSTER_NAME))
    self.AssertErrContains('argument --maintenance-window')

  def testCreateLocalSsdVolumeConfig(self):
    m = self.messages
    format_enum = self.messages.LocalSsdVolumeConfig.FormatValueValuesEnum
    cluster_kwargs = {
        'name':
            'localssdvolumeconfig-cluster',
        'localSsdVolumeConfigs': [
            m.LocalSsdVolumeConfig(count=1, type='scsi', format=format_enum.FS)
        ],
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(
                self.API_VERSION, self.PROJECT_NUM, self.ZONE, cluster_kwargs[
                    'name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create localssdvolumeconfig-cluster '
        '--local-ssd-volumes count=1,type="scsi",format="fs"'
        )

  @parameterized.parameters(
      (1, 'notatype', 'fs'),
      (4, 'scsi', 'notaformat'),
      ('notacount', 'scsi', 'fs'),
      (0, 'scsi', 'fs'))
  def testCreateInvalidLocalSsdVolumeConfig(self, ssd_count, ssd_type,
                                            ssd_format):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --local-ssd-volumes count={1},type={2},format={3}'.
          format(self.CLUSTER_NAME, ssd_count, ssd_type, ssd_format))
    self.AssertErrContains('argument --local-ssd-volumes')

  def testCreateEmptyLocalSsdVolumeConfig(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --local-ssd-volumes'.format(self.CLUSTER_NAME))
    self.AssertErrContains('argument --local-ssd-volumes')

  def testEnableTpu(self):
    cluster_kwargs = {
        'enableKubernetesAlpha': True,
        'enableTpu': True,
    }
    # Cluster create returns operation pending
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    policy = self._MakeIPAllocationPolicy(
        useIpAliases=True,
        createSubnetwork=False,
        tpuIpv4Cidr='10.1.0.0/20',
    )
    expected_cluster.ipAllocationPolicy = policy
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-kubernetes-alpha '
        '--enable-ip-alias '
        '--enable-tpu '
        '--tpu-ipv4-cidr 10.1.0.0/20 '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  @parameterized.parameters(
      ('--enable-tpu',
       api_adapter.PREREQUISITE_OPTION_ERROR_MSG.format(
           prerequisite='enable-kubernetes-alpha', opt='enable-tpu')),
      ('--enable-ip-alias --enable-tpu',
       api_adapter.PREREQUISITE_OPTION_ERROR_MSG.format(
           prerequisite='enable-kubernetes-alpha', opt='enable-tpu')),
      ('--enable-kubernetes-alpha --enable-tpu',
       api_adapter.PREREQUISITE_OPTION_ERROR_MSG.format(
           prerequisite='enable-ip-alias', opt='enable-tpu')),
      ('--enable-ip-alias --tpu-ipv4-cidr=10.1.0.0/20',
       api_adapter.PREREQUISITE_OPTION_ERROR_MSG.format(
           prerequisite='enable-tpu', opt='tpu-ipv4-cidr')),
      ('--tpu-ipv4-cidr=10.1.0.0/20',
       api_adapter.PREREQUISITE_OPTION_ERROR_MSG.format(
           prerequisite='enable-tpu', opt='tpu-ipv4-cidr')),
  )
  def testEnableTpuBadArgs(self, flags, expected_msg):
    command = (
        self.clusters_command_base.format(self.ZONE) +
        ' create {name} --quiet '.format(name=self.CLUSTER_NAME) + flags)
    self.AssertRaisesExceptionMatches(c_util.Error, expected_msg, self.Run,
                                      command)

  def testCreateEnableAddonsIstio(self):
    mtls = self.messages.IstioConfig.AuthValueValuesEnum.AUTH_MUTUAL_TLS
    cluster_kwargs = {
        'addonsConfig': self.msgs.AddonsConfig(
            httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=False),
            horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                disabled=True),
            kubernetesDashboard=self.msgs.KubernetesDashboard(
                disabled=False),
            networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                disabled=True),
            istioConfig=self.msgs.IstioConfig(
                disabled=False,
                auth=mtls)),
    }
    self.ExpectCreateCluster(self._MakeCluster(**cluster_kwargs),
                             self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.7.0'))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --addons=HttpLoadBalancing,KubernetesDashboard,Istio'
        ' --istio-config=auth=mutual_tls'
        .format(self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testCreateEnableAddonsIstioNoAuth(self):
    auth = self.messages.IstioConfig.AuthValueValuesEnum.AUTH_NONE
    cluster_kwargs = {
        'addonsConfig': self.msgs.AddonsConfig(
            httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=False),
            horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                disabled=True),
            kubernetesDashboard=self.msgs.KubernetesDashboard(
                disabled=False),
            networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                disabled=True),
            istioConfig=self.msgs.IstioConfig(
                disabled=False,
                auth=auth)),
    }
    self.ExpectCreateCluster(self._MakeCluster(**cluster_kwargs),
                             self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.7.0'))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --addons=HttpLoadBalancing,KubernetesDashboard,Istio'
        .format(self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testCreateDisableAddonsIstio(self):
    cluster_kwargs = {
        'addonsConfig': self.msgs.AddonsConfig(
            httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=False),
            horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                disabled=True),
            kubernetesDashboard=self.msgs.KubernetesDashboard(
                disabled=False),
            networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                disabled=True)),
    }
    self.ExpectCreateCluster(self._MakeCluster(**cluster_kwargs),
                             self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.7.0'))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --addons=HttpLoadBalancing,KubernetesDashboard'
        .format(self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testCreateValidateAddonsIstioConfig(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --addons=HttpLoadBalancing,KubernetesDashboard,Istio'
          ' --istio-config=auth=mutal_tls'
          .format(self.CLUSTER_NAME))
    self.AssertErrContains('auth is either NONE or MUTUAL_TLS')

  def testCreateValidateAddonsIstio(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --addons=HttpLoadBalancing,KubernetesDashboard'
          ' --istio-config=auth=mutual_tls'
          .format(self.CLUSTER_NAME))
    self.AssertErrContains('--addon=Istio must be specified')


if __name__ == '__main__':
  test_case.main()
