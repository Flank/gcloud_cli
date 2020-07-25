# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
from __future__ import division
from __future__ import unicode_literals

import json
import os

from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import kubeconfig as kconfig
from googlecloudsdk.api_lib.container import util as c_util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import constants
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.container import base

from six.moves import range  # pylint: disable=redefined-builtin


class CreateTestGA(parameterized.TestCase, base.GATestBase,
                   base.ClustersTestBase):
  """gcloud GA track using container v1 API."""

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
    cluster_kwargs = {}
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
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
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, location, self.PROJECT_ID))
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
    self.AssertErrContains('Created')
    c_config = c_util.ClusterConfig.Load(self.CLUSTER_NAME, location,
                                         self.PROJECT_ID)
    self._TestDefaultAuth(c_config)
    self.AssertErrContains(
        c_util.KUBECONFIG_USAGE_FMT.format(
            cluster=self.CLUSTER_NAME, context=c_config.kube_context))
    self.assertIsNone(properties.VALUES.container.cluster.Get())

  def testCreateDefaults(self):
    self.WriteInput('y')
    self._TestCreateDefaults(self.ZONE)

  def testCreateDefaultsRegional(self):
    self.WriteInput('y\ny')
    self._TestCreateDefaults(self.REGION)

  def testCreateDefaultsJsonOutput(self):
    self.ExpectCreateCalls()
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                  self.PROJECT_ID))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --format json'.format(self.CLUSTER_NAME))
    result = json.loads(self.GetOutput())
    json_cluster = result[0]
    self.assertEqual(json_cluster['status'], str(self.running))

  def testCreateAsync(self):
    # Create cluster returns operation pending
    cluster_kwargs = {}
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
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
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                  self.PROJECT_ID))
    self.AssertOutputContains(str(cluster.status))
    self.AssertErrNotContains('Created')
    self.AssertErrNotContains('kubeconfig')
    self.assertIsNone(properties.VALUES.container.cluster.Get())

  def testCreateNoDefaults(self, additional_cluster_kwargs=None):
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
                autoRepair=False, autoUpgrade=False, upgradeOptions=None),
        'authorizedNetworks':
            self.msgs.MainAuthorizedNetworksConfig(
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
        'issueClientCertificate':
            False,
        'metadata':
            self.msgs.NodeConfig.MetadataValue(additionalProperties=[
                self.msgs.NodeConfig.MetadataValue.AdditionalProperty(
                    key=key, value=value)
                for key, value in [('key', 'value'), ('key2', 'value2')]
            ]),
        'verticalPodAutoscaling':
            self.msgs.VerticalPodAutoscaling(enabled=True),
    }
    if additional_cluster_kwargs is not None:
      for key, value in additional_cluster_kwargs.items():
        cluster_kwargs[key] = value

    def n(pool_index):
      return self._MakeDefaultNodePool(
          nodePoolName='default-pool-{pool}'.format(pool=pool_index),
          initialNodeCount=500 if pool_index < 3 else 499,
          **cluster_kwargs)

    cluster_kwargs['nodePools'] = [n(pool_index) for pool_index in range(4)]
    # Cluster create returns operation pending
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs.copy()
    self.updateResponse(
        return_args,
        currentMainVersion=cluster_kwargs['clusterApiVersion'],
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
        '--no-enable-stackdriver-kubernetes '
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
        '--no-enable-autorepair '
        '--no-enable-autoupgrade '
        '--enable-main-authorized-networks '
        '--main-authorized-networks=10.0.0.1/32,10.0.0.2/32 '
        '--no-issue-client-certificate '
        '--metadata key=value,key2=value2 '
        '--enable-vertical-pod-autoscaling'.format(**cluster_kwargs))
    self.AssertOutputMatches(
        (r'NAME LOCATION MASTER_VERSION MASTER_IP MACHINE_TYPE NODE_VERSION '
         'NUM_NODES STATUS\n'
         '{name} {zone} {version} {endpoint} {node_type} {node_version} '
         '{num_nodes} {status}\\n').format(
             name=return_cluster.name,
             zone=return_cluster.zone,
             version=return_cluster.initialClusterVersion,
             endpoint=return_cluster.endpoint,
             node_type=return_cluster.nodePools[0].config.machineType,
             num_nodes=return_cluster.currentNodeCount,
             node_version=return_cluster.currentNodeVersion,
             status=return_cluster.status,
         ),
        normalize_space=True)
    # Note: We use ErrContains rather than ErrEquals because this command can
    # have a warning at the top depending on if kubectl is currently available,
    # which can vary depending on environment.
    self.AssertErrContains("""This will disable the autorepair feature for \
nodes. Please see \
https://cloud.google.com/kubernetes-engine/docs/node-auto-repair for more \
information on node autorepairs.
{{"ux": "PROGRESS_TRACKER", "message": "Creating cluster my-little-cluster-kubernetes-is-magic in us-central1-f", "status": "SUCCESS"}}
Created [https://container.googleapis.com/{0}/projects/fake-project-id/zones/us-central1-f/clusters/my-little-cluster-kubernetes-is-magic].
To inspect the contents of your cluster, go to: https://console.cloud.google.com/kubernetes/workload_/gcloud/us-central1-f/my-little-cluster-kubernetes-is-magic?project=fake-project-id
kubeconfig entry generated for my-little-cluster-kubernetes-is-magic.
""".format(self.API_VERSION))
    c_config = c_util.ClusterConfig.Load(cluster_kwargs['name'], self.ZONE,
                                         self.PROJECT_ID)
    self._TestDefaultAuth(c_config)

  def testCreateEnableAddons(self):
    cluster_kwargs = {
        'addonsConfig':
            self.msgs.AddonsConfig(
                httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=False),
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=True),
                kubernetesDashboard=self.msgs.KubernetesDashboard(
                    disabled=False),
                networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                    disabled=True)),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.7.0'))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --addons=HttpLoadBalancing,KubernetesDashboard'.format(
            self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

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

  def testServiceAccountCloudPlatformScopes(self):
    cluster_kwargs = {
        'serviceAccount':
            'my-sa',
        'oauthScopes': [
            'https://www.googleapis.com/auth/cloud-platform',
            'https://www.googleapis.com/auth/userinfo.email'
        ],
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

  def testServiceAccountCustomScopes(self):
    cluster_kwargs = {
        'serviceAccount': 'my-sa',
        'oauthScopes': ['something-else'],
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
             '--scopes=something-else '
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
    cluster_kwargs = {}
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.3.0'))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0}'.format(self.CLUSTER_NAME))
    c_config = c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                         self.PROJECT_ID)
    self._TestDefaultAuth(c_config)

  # TODO(b/70856999) Test creation with client cert auth.

  def testCreateADCAuth(self):
    properties.VALUES.container.use_app_default_credentials.Set(True)
    cluster_kwargs = {}
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.3.0'))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0}'.format(self.CLUSTER_NAME))
    c_config = c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                         self.PROJECT_ID)
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
    self.ExpectGetOperation(
        self._MakeOperation(status=self.op_done, detail=msg))
    # Get cluster returns valid cluster
    self.ExpectGetCluster(self._RunningCluster())
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                  self.PROJECT_ID))
    # Set an initial current-context in kubeconfig to verify we overwrite it
    initial = kconfig.Kubeconfig.Default()
    initial.SetCurrentContext('current-context')
    initial.SaveToFile()
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0}'.format(self.CLUSTER_NAME))
    cluster = self._RunningCluster()
    c_config = c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                         self.PROJECT_ID)
    self._TestDefaultAuth(c_config)
    self.AssertOutputContains(str(cluster.status))
    self.AssertOutputContains(str(cluster.endpoint))
    self.AssertErrContains('Created')
    self.AssertErrContains(
        c_util.KUBECONFIG_USAGE_FMT.format(
            cluster=self.CLUSTER_NAME, context=c_config.kube_context))
    self.assertIsNone(properties.VALUES.container.cluster.Get())
    self.assertEqual(kconfig.Kubeconfig.Default().current_context,
                     c_config.kube_context)
    self.AssertErrContains(msg)

  def testCreateMissingEnv(self):
    # HOME is set to a tmp directory in UnitTestBase.
    # Temporarily unset HOME so we can verify expected warning.
    self.assertEqual(self.tmp_home.path, os.environ['HOME'])
    self.ExpectCreateCalls()
    self.StartDictPatch('os.environ', {
        'HOME': '',
        'HOMEDRIVE': '',
        'HOMEPATH': '',
        'USERPROFILE': ''
    })
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
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --num-nodes=-1'.format(self.CLUSTER_NAME))
    self.AssertErrContains('argument --num-nodes')

  def testCreateInvalidNodeLabels(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --node-labels=test=a,b'.format(self.CLUSTER_NAME))
    self.AssertErrContains('argument --node-labels')

  def testCreateInvalidNodeTaints(self):
    with self.assertRaises(c_util.Error):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --node-taints=test=ab'.format(self.CLUSTER_NAME))
    self.AssertErrContains('argument --node-taints')

  def testCreateInvalidNodeTaintEffect(self):
    with self.assertRaises(c_util.Error):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --node-taints=test=ab:RandomEffect'.format(
              self.CLUSTER_NAME))
    self.AssertErrContains('argument --node-taints')

  def testCreateEmptyTags(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --tags='.format(self.CLUSTER_NAME))
    self.AssertErrContains('argument --tags')

  def testCreateZeroNodes(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --num-nodes=0'.format(self.CLUSTER_NAME))
    self.AssertErrContains('argument --num-nodes')

  def testCreateUnauthorized(self):
    cluster_kwargs = {}
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), exception=base.UNAUTHORIZED_ERROR)
    with self.assertRaises(exceptions.HttpException):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --async'.format(self.CLUSTER_NAME))
    self.AssertErrContains('code=403, message=unauthorized')

  def testCreateGetOperationUnauthorized(self):
    cluster_kwargs = {}
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
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

  def testCreateMainAuthorizedNetworksDisable(self):
    cluster_kwargs = {
        'authorizedNetworks':
            self.messages.MainAuthorizedNetworksConfig(enabled=False),
    }
    # Cluster create returns operation pending
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--no-enable-main-authorized-networks'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testCreateInvalidMainAuthorizedNetworksWithoutEnable(self):
    with self.assertRaises(c_util.Error):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --main-authorized-networks=10.0.0.1/32'.format(
              self.CLUSTER_NAME))
      self.AssertErrContains('Cannot use --main-authorized-networks')

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

  @parameterized.parameters('--username=admin', '--enable-basic-auth')
  def testEnableBasicAuth(self, flags):
    cluster_kwargs = {
        'username': 'admin',
    }
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
    cluster_kwargs = {
        'username': '',
    }
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
    expected_cluster.mainAuth = self.messages.MainAuth(
        clientCertificateConfig=(self.messages.ClientCertificateConfig(
            issueClientCertificate=expect_issue)))
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(return_cluster)
    self.Run('{base} create {name} {flags} '
             '--quiet'.format(
                 base=self.clusters_command_base.format(self.ZONE),
                 name=self.CLUSTER_NAME,
                 flags=flags))

  @parameterized.parameters(('', '', True), ('--image-type', 'COS', True),
                            ('--image-type', 'UBUNTU', False))
  def testAutoRepairDefaults(self, image_flag, image_value, expect_autorepair):
    cluster_kwargs = {
        'management': self._MakeDefaultNodeManagement(expect_autorepair),
        'imageType': image_value if image_value else None,
    }
    expected_cluster, return_cluster = self.makeExpectedAndReturnClusters(
        cluster_kwargs)
    # Create cluster expects cluster and returns pending operation.
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    # Get operation returns done operation.
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns expected cluster, populated with other fields by server.
    self.ExpectGetCluster(return_cluster)
    self.Run('{base} create {name} {flag} {value} '
             '--quiet'.format(
                 base=self.clusters_command_base.format(self.ZONE),
                 name=self.CLUSTER_NAME,
                 flag=image_flag,
                 value=image_value))

  def testCreateInvalidAcceleratorMissingType(self):
    properties.VALUES.core.disable_prompts.Set(False)
    with self.AssertRaisesArgumentErrorMatches(
        r'argument --accelerator: Key [type] required in dict arg but not '
        r'provided'):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --accelerator=count=2'.format(self.CLUSTER_NAME))

  def testCreateWithValidAccelerators(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'my-gpu-cluster',
        'accelerators': [
            m.AcceleratorConfig(
                acceleratorType='nvidia-tesla-k80', acceleratorCount=int(2))
        ],
    }
    cluster_kwargs['nodePools'] = [
        self._MakeDefaultNodePool(
            nodePoolName='default-pool', initialNodeCount=500, **cluster_kwargs)
    ]
    # Cluster create returns operation pending
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
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
        '--accelerator=type=nvidia-tesla-k80,count=2')
    self.AssertOutputMatches(
        (r'NAME LOCATION MASTER_VERSION MASTER_IP MACHINE_TYPE NODE_VERSION '
         'NUM_NODES STATUS\n'
         '{name} {zone} {endpoint} '
         '{num_nodes} {status}\\n').format(
             name=return_cluster.name,
             num_nodes=return_cluster.currentNodeCount,
             zone=return_cluster.zone,
             endpoint=return_cluster.endpoint,
             status=return_cluster.status,
         ),
        normalize_space=True)

  def testAcceleratorCountDefaulting(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'my-gpu-cluster',
        'accelerators': [
            m.AcceleratorConfig(
                acceleratorType='nvidia-tesla-k80', acceleratorCount=int(1))
        ],
    }
    cluster_kwargs['nodePools'] = [
        self._MakeDefaultNodePool(
            nodePoolName='default-pool', initialNodeCount=500, **cluster_kwargs)
    ]
    # Cluster create returns operation pending
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
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
         '{num_nodes} {status}\\n').format(
             name=return_cluster.name,
             num_nodes=return_cluster.currentNodeCount,
             zone=return_cluster.zone,
             endpoint=return_cluster.endpoint,
             status=return_cluster.status,
         ),
        normalize_space=True)

  def testCreateWithMetadataFromFile(self):
    cluster_kwargs = {
        'metadata':
            self.msgs.NodeConfig.MetadataValue(
                additionalProperties=[
                    self.msgs.NodeConfig.MetadataValue.AdditionalProperty(
                        key='file_key', value='file_value'),
                ],),
    }
    md_file_path = self.Touch(self.temp_path, contents='file_value')

    # Cluster create returns operation pending
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs.copy()
    self.updateResponse(
        return_args, clusterApiVersion='0.18.2', currentMainVersion1='0.18.2')
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--metadata-from-file file_key={path}'.format(
            name=self.CLUSTER_NAME, path=md_file_path))
    self.AssertOutputContains('RUNNING')

  def testEnablePrivateNodes(self):
    cluster_kwargs = {
        'name': self.CLUSTER_NAME,
    }

    expected_cluster = self._MakeCluster(**cluster_kwargs)
    policy = self._MakeIPAllocationPolicy(
        createSubnetwork=False,
        useIpAliases=True,
    )
    expected_cluster.ipAllocationPolicy = policy
    config = self._MakePrivateClusterConfig(
        enablePrivateNodes=True, mainIpv4Cidr='172.16.10.0/28')
    expected_cluster.privateClusterConfig = config
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)

    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-ip-alias '
        '--enable-private-nodes '
        '--main-ipv4-cidr=172.16.10.0/28 '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testEnablePrivateEndpoint(self):
    cluster_kwargs = {
        'name': self.CLUSTER_NAME,
    }

    expected_cluster = self._MakeCluster(**cluster_kwargs)
    policy = self._MakeIPAllocationPolicy(
        createSubnetwork=False,
        useIpAliases=True,
    )
    expected_cluster.ipAllocationPolicy = policy
    config = self._MakePrivateClusterConfig(
        enablePrivateNodes=True,
        enablePrivateEndpoint=True,
        mainIpv4Cidr='172.16.10.0/28')
    expected_cluster.privateClusterConfig = config
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)

    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-ip-alias '
        '--enable-private-nodes '
        '--enable-private-endpoint '
        '--main-ipv4-cidr=172.16.10.0/28 '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testNodeModificationWarning(self):
    cluster_kwargs = {
        'imageType': 'ubuntu',
    }
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
    self.Run(
        '{base} create {name} --image-type=ubuntu --enable-autorepair'.format(
            base=self.clusters_command_base.format(self.ZONE),
            name=self.CLUSTER_NAME))
    self.AssertErrContains('Created')
    self.AssertErrContains(
        'Modifications on the boot disks of node VMs do not persist across '
        'node recreations. Nodes are recreated during manual-upgrade, '
        'auto-upgrade, auto-repair, and auto-scaling. To preserve '
        'modifications across node recreation, use a DaemonSet.')

  def testDefaultMaxPodsConstraint(self):
    cluster_kwargs = {
        'defaultMaxPodsConstraint':
            self.msgs.MaxPodsConstraint(maxPodsPerNode=30),
        'maxPodsConstraint':
            self.msgs.MaxPodsConstraint(maxPodsPerNode=60),
    }
    # Cluster create returns operation pending
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    policy = self._MakeIPAllocationPolicy(
        clusterIpv4Cidr=None, createSubnetwork=False, useIpAliases=True)
    expected_cluster.ipAllocationPolicy = policy
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs.copy()
    self.updateResponse(
        return_args,
        ipAllocationPolicy=policy,
        maxPodsConstraint=cluster_kwargs.get('maxPodsConstraint'))
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-ip-alias '
        '--default-max-pods-per-node=30 '
        '--max-pods-per-node=60 '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testDefaultMaxPodsConstraintBadArgs(self):
    command = (
        self.clusters_command_base.format(self.ZONE) +
        ' create {name} --quiet --default-max-pods-per-node=30'.format(
            name=self.CLUSTER_NAME))
    self.AssertRaisesExceptionMatches(
        c_util.Error,
        api_adapter.DEFAULT_MAX_PODS_PER_NODE_WITHOUT_IP_ALIAS_ERROR_MSG,
        self.Run, command)

  def testEnableStackdriverKubernetes(self):
    cluster_kwargs = {
        'loggingService': 'logging.googleapis.com/kubernetes',
        'monitoringService': 'monitoring.googleapis.com/kubernetes',
    }
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
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-stackdriver-kubernetes '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testEnableBinauthz(self):
    cluster_kwargs = {
        'binaryAuthorization': self.messages.BinaryAuthorization(enabled=True),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(),
    )
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-binauthz '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testEnableTpu(self):
    cluster_kwargs = {
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
        '--enable-ip-alias '
        '--enable-tpu '
        '--tpu-ipv4-cidr 10.1.0.0/20 '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  @parameterized.parameters(
      ('--enable-tpu',
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

  def testEnableIntraNodeVisibility(self):
    cluster_kwargs = {
        'enableIntraNodeVisibility': True,
    }
    # Cluster create returns operation pending
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    expected_cluster.networkConfig = self.messages.NetworkConfig(
        enableIntraNodeVisibility=True)
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
        '--enable-intra-node-visibility '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testResourceUsageExportConfig(self):
    self._TestResourceUsageExportConfig('', None)
    self._TestResourceUsageExportConfig(
        '--resource-usage-bigquery-dataset=dataset_id',
        self.messages.ResourceUsageExportConfig(
            bigqueryDestination=self.messages.BigQueryDestination(
                datasetId='dataset_id'),
            consumptionMeteringConfig=None))
    self._TestResourceUsageExportConfig(
        '--resource-usage-bigquery-dataset=dataset_id '
        '--no-enable-network-egress-metering',
        self.messages.ResourceUsageExportConfig(
            bigqueryDestination=self.messages.BigQueryDestination(
                datasetId='dataset_id'),
            consumptionMeteringConfig=None))
    self._TestResourceUsageExportConfig(
        '--resource-usage-bigquery-dataset=dataset_id '
        '--enable-network-egress-metering',
        self.messages.ResourceUsageExportConfig(
            bigqueryDestination=self.messages.BigQueryDestination(
                datasetId='dataset_id'),
            enableNetworkEgressMetering=True,
            consumptionMeteringConfig=None))
    self._TestResourceUsageExportConfig(
        '--resource-usage-bigquery-dataset=dataset_id '
        '--enable-resource-consumption-metering',
        self.messages.ResourceUsageExportConfig(
            bigqueryDestination=self.messages.BigQueryDestination(
                datasetId='dataset_id'),
            consumptionMeteringConfig=self.messages.ConsumptionMeteringConfig(
                enabled=True)))
    self._TestResourceUsageExportConfig(
        '--resource-usage-bigquery-dataset=dataset_id '
        '--no-enable-resource-consumption-metering',
        self.messages.ResourceUsageExportConfig(
            bigqueryDestination=self.messages.BigQueryDestination(
                datasetId='dataset_id'),
            consumptionMeteringConfig=self.messages.ConsumptionMeteringConfig(
                enabled=False)))

  def _TestResourceUsageExportConfig(self, flags, export_config):
    expected_cluster, return_cluster = self.makeExpectedAndReturnClusters({})
    expected_cluster.resourceUsageExportConfig = export_config
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(return_cluster)
    self.Run('{base} create {name} {flags} --quiet'.format(
        base=self.clusters_command_base.format(self.ZONE),
        name=self.CLUSTER_NAME,
        flags=flags))

  def testResourceUsageExportConfigInvalid(self):
    with self.AssertRaisesExceptionMatches(
        c_util.Error, api_adapter.ENABLE_NETWORK_EGRESS_METERING_ERROR_MSG):
      self.Run('{base} create {name} --quiet {flag}'.format(
          base=self.clusters_command_base.format(self.ZONE),
          name=self.CLUSTER_NAME,
          flag='--enable-network-egress-metering'))
    with self.AssertRaisesExceptionMatches(
        c_util.Error,
        api_adapter.ENABLE_RESOURCE_CONSUMPTION_METERING_ERROR_MSG):
      self.Run('{base} create {name} --quiet {flag}'.format(
          base=self.clusters_command_base.format(self.ZONE),
          name=self.CLUSTER_NAME,
          flag='--enable-resource-consumption-metering'))

  def testCreateDailyMaintenanceWindow(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'mw-cluster',
        'maintenancePolicy':
            m.MaintenancePolicy(
                window=m.MaintenanceWindow(
                    dailyMaintenanceWindow=m.DailyMaintenanceWindow(
                        startTime='11:43'))),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create mw-cluster --maintenance-window=11:43')

  def testCreateEmptyDailyMaintenanceWindow(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --maintenance-window: expected one argument'):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --maintenance-window'.format(self.CLUSTER_NAME))

  def testCreateInvalidDailyMaintenanceWindow(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --maintenance-window=24:93'.format(self.CLUSTER_NAME))
    self.AssertErrContains('argument --maintenance-window')

  def testCreateRecurringMaintenanceWindow(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'mw-cluster',
        'maintenancePolicy':
            m.MaintenancePolicy(
                window=m.MaintenanceWindow(
                    recurringWindow=m.RecurringTimeWindow(
                        window=m.TimeWindow(
                            startTime='2000-01-01T09:00:00+00:00',
                            endTime='2000-01-01T17:00:00+00:00'),
                        recurrence='FREQ=WEEKLY;BYDAY=MO,WE,FR')))
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create mw-cluster '
        '--maintenance-window-start=2000-01-01T09:00:00Z '
        '--maintenance-window-end=2000-01-01T17:00:00Z '
        '--maintenance-window-recurrence=FREQ=WEEKLY;BYDAY=MO,WE,FR')

  @parameterized.parameters(
      ('--maintenance-window-start=2000-01-01T09:00:00Z '
       '--maintenance-window-recurrence=FREQ=DAILY',
       '--maintenance-window-end'),
      ('--maintenance-window-end=2000-01-01T17:00:00Z '
       '--maintenance-window-recurrence=FREQ=DAILY',
       '--maintenance-window-start'),
      ('--maintenance-window-start=2000-01-01T09:00:00Z '
       '--maintenance-window-end=2000-01-01T17:00:00Z',
       '--maintenance-window-recurrence'),
  )
  def testCreateRecurringMaintenanceWindowMissingFields(self, flags,
                                                        error_flag):
    with self.AssertRaisesArgumentErrorMatches(
        'argument {0}: Must be specified.'.format(error_flag)):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create mw-cluster {0}'.format(flags))

  def testCreateMaintenanceWindowMutexGroup(self):
    with self.AssertRaisesArgumentErrorMatches('At most one of'):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create mw-cluster --maintenance-window=00:00 '
          '--maintenance-window-start=2000-01-01T00:00:00Z '
          '--maintenance-window-end=2000-01-01T04:00:00Z '
          '--maintenance-window-recurrence=FREQ=DAILY')

  def testEnableDatabaseEncryption(self):
    cluster_kwargs = {
        'databaseEncryptionKey':
            'projects/p/locations/l/keyRings/kr/cryptoKeys/k',
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--database-encryption-key=projects/p/locations/l/keyRings/kr/cryptoKeys/k'
        .format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testInvalidDatabaseEncryptionKey(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' create {name} '
          '--database-encryption-key=projects/p'.format(name=self.CLUSTER_NAME))
    self.AssertErrContains(
        'Must be in format of \'projects/[KEY_PROJECT_ID]/locations/[LOCATION]/keyRings/[RING_NAME]/cryptoKeys/[KEY_NAME]\''
    )

  def testCreateResourceLimits(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'rl-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(oauthScopes=[],),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', minimum=10, maximum=20),
                    m.ResourceLimit(
                        resourceType='memory', minimum=16, maximum=128)
                ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--enable-autoprovisioning --min-cpu 10 --max-cpu 20 '
        '--min-memory 16 --max-memory 128')

  def testCreateResourceLimitsFromFile(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'rl-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(oauthScopes=[],),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', minimum=1, maximum=2),
                    m.ResourceLimit(
                        resourceType='memory', minimum=10, maximum=20),
                    m.ResourceLimit(
                        resourceType='nvidia-tesla-k80', minimum=1, maximum=2),
                    m.ResourceLimit(
                        resourceType='nvidia-tesla-p100', minimum=0, maximum=1)
                ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    autoprovisioning_config = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
resourceLimits:
  - resourceType: 'cpu'
    minimum: 1
    maximum: 2
  - resourceType: 'memory'
    minimum: 10
    maximum: 20
  - resourceType: 'nvidia-tesla-k80'
    minimum: 1
    maximum: 2
  - resourceType: 'nvidia-tesla-p100'
    minimum: 0
    maximum: 1
        """)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--enable-autoprovisioning '
        '--autoprovisioning-config-file {}'.format(autoprovisioning_config))

  def testCreateAutoprovisioningServiceAccountFromFile(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'rl-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(
                    serviceAccount='sa1',
                    oauthScopes=[],
                ),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', minimum=1, maximum=2),
                    m.ResourceLimit(
                        resourceType='memory', minimum=10, maximum=20),
                ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    autoprovisioning_config = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
serviceAccount: sa1
resourceLimits:
  - resourceType: 'cpu'
    minimum: 1
    maximum: 2
  - resourceType: 'memory'
    minimum: 10
    maximum: 20
        """)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--enable-autoprovisioning '
        '--autoprovisioning-config-file {}'.format(autoprovisioning_config))

  def testCreateAutoprovisioningServiceAccountAndScopes(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'rl-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(
                    serviceAccount='sa1',
                    oauthScopes=['scope1', 'scope2'],
                ),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', minimum=10, maximum=20),
                    m.ResourceLimit(
                        resourceType='memory', minimum=16, maximum=128)
                ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--enable-autoprovisioning --min-cpu 10 --max-cpu 20 '
        '--autoprovisioning-service-account=sa1 '
        '--autoprovisioning-scopes=scope1,scope2 '
        '--min-memory 16 --max-memory 128')

  def testCreateAutoprovisioningServiceAccount(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'rl-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(
                    serviceAccount='sa1',
                    oauthScopes=[],
                ),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', minimum=10, maximum=20),
                    m.ResourceLimit(
                        resourceType='memory', minimum=16, maximum=128)
                ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--enable-autoprovisioning --min-cpu 10 --max-cpu 20 '
        '--autoprovisioning-service-account=sa1 '
        '--min-memory 16 --max-memory 128')

  def testCreateAutoprovisioningScopesFromFile(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'rl-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(
                    oauthScopes=['scope1', 'scope2'],),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', minimum=1, maximum=2),
                    m.ResourceLimit(
                        resourceType='memory', minimum=10, maximum=20),
                ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    autoprovisioning_config = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
scopes:
  - scope1
  - scope2
resourceLimits:
  - resourceType: 'cpu'
    minimum: 1
    maximum: 2
  - resourceType: 'memory'
    minimum: 10
    maximum: 20
        """)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--enable-autoprovisioning '
        '--autoprovisioning-config-file {}'.format(autoprovisioning_config))

  def testCreateAutoprovisioningScopes(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'rl-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(
                    oauthScopes=['scope1', 'scope2'],),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', minimum=10, maximum=20),
                    m.ResourceLimit(
                        resourceType='memory', minimum=16, maximum=128)
                ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--enable-autoprovisioning --min-cpu 10 --max-cpu 20 '
        '--autoprovisioning-scopes=scope1,scope2 '
        '--min-memory 16 --max-memory 128')

  def testCreateAutoprovisioningLocationsFromFile(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'rl-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningLocations=['us-central1-a', 'us-central1-b'],
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(oauthScopes=[],),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', minimum=1, maximum=2),
                    m.ResourceLimit(
                        resourceType='memory', minimum=10, maximum=20),
                ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    autoprovisioning_config = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
autoprovisioningLocations:
  - us-central1-a
  - us-central1-b
resourceLimits:
  - resourceType: 'cpu'
    minimum: 1
    maximum: 2
  - resourceType: 'memory'
    minimum: 10
    maximum: 20
        """)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--enable-autoprovisioning '
        '--autoprovisioning-config-file {}'.format(autoprovisioning_config))

  def testCreateAutoprovisioningLocations(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'rl-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningLocations=['us-central1-a', 'us-central1-b'],
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(oauthScopes=[],),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', minimum=10, maximum=20),
                    m.ResourceLimit(
                        resourceType='memory', minimum=16, maximum=128)
                ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--enable-autoprovisioning --min-cpu 10 --max-cpu 20 '
        '--min-memory 16 --max-memory 128 '
        '--autoprovisioning-locations=us-central1-a,us-central1-b ')

  def testCreateEnableAddonsCloudRunWithoutStackdriverKubernetes(self):
    logging = 'Cloud Logging'
    monitoring = 'Cloud Monitoring'
    err_msg = ('The CloudRun-on-GKE addon (--addons=CloudRun) requires %s and '
               '%s to be enabled via the --enable-stackdriver-kubernetes flag.'
              ) % (logging, monitoring)
    with self.AssertRaisesExceptionMatches(c_util.Error, err_msg):
      self.Run((self.clusters_command_base.format(self.ZONE) +
                ' create {0} --addons=CloudRun').format(self.CLUSTER_NAME))

  def testAutoUpgradeDefault(self):
    cluster_kwargs = {
        'management':
            self.messages.NodeManagement(autoRepair=True, autoUpgrade=True)
    }
    expected_cluster, return_cluster = self.makeExpectedAndReturnClusters(
        cluster_kwargs)
    # Create cluster expects cluster and returns pending operation.
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    # Get operation returns done operation.
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns expected cluster, populated with other fields by server.
    self.ExpectGetCluster(return_cluster)
    self.Run('{base} create {name} --quiet'.format(
        base=self.clusters_command_base.format(self.ZONE),
        name=self.CLUSTER_NAME))

  @parameterized.parameters(('any', ''), ('none', ''),
                            ('specific', 'reservation-specific'))
  def testReservationAffinity(self, affinity, reservation_name):
    cluster_kwargs = {
        'reservationAffinity':
            self._MakeReservationAffinity(affinity, reservation_name)
    }
    cluster_kwargs['nodePools'] = [
        self._MakeDefaultNodePool(
            nodePoolName='default-pool', **cluster_kwargs)
    ]
    expected_cluster, return_cluster = self.makeExpectedAndReturnClusters(
        cluster_kwargs)
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(return_cluster)

    reservation_flags = '--reservation-affinity={}'.format(affinity)
    if affinity == 'specific':
      reservation_flags += ' --reservation={}'.format(reservation_name)
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} {1}'.format(self.CLUSTER_NAME, reservation_flags))

  @parameterized.parameters('any', 'none')
  def testNonSpecificReservationWithReservationName(self, affinity):
    reservation_name = 'reservation_name'
    err_msg = 'Cannot specify --reservation for --reservation-affinity={}.'.format(
        affinity)
    with self.AssertRaisesExceptionMatches(c_util.Error, err_msg):
      self.Run(
          (self.clusters_command_base.format(self.ZONE) +
           ' create {0} --reservation-affinity={1} --reservation={2}').format(
               self.CLUSTER_NAME, affinity, reservation_name))

  def testCreateWithReservationSpecificWithoutReservationName(self):
    err_msg = 'Must specify --reservation for --reservation-affinity=specific.'
    with self.AssertRaisesExceptionMatches(c_util.Error, err_msg):
      self.Run((self.clusters_command_base.format(self.ZONE) +
                ' create {0} --reservation-affinity=specific').format(
                    self.CLUSTER_NAME))

  def testWorkloadIdentityConfig(self):
    expected_cluster, return_cluster = self.makeExpectedAndReturnClusters({})
    expected_cluster.workloadIdentityConfig = self.messages.WorkloadIdentityConfig(
        workloadPool='{}.svc.id.goog'.format(self.PROJECT_ID))
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(return_cluster)
    self.Run(
        '{base} create {name} --workload-pool={project}.svc.id.goog'.format(
            base=self.clusters_command_base.format(self.ZONE),
            name=self.CLUSTER_NAME,
            project=self.PROJECT_ID))
    self.AssertOutputContains('RUNNING')

  def testEnableShieldedNodes(self):
    cluster_kwargs = {
        'shieldedNodes': self.messages.ShieldedNodes(enabled=True),
        # TODO(b/126960310): Remove unrelated node management config.
    }
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)

    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-shielded-nodes '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testShieldedNodesEnabledByDefaultWarning(self):
    cluster_kwargs = {}
    expected_cluster, return_cluster = self.makeExpectedAndReturnClusters(
        cluster_kwargs)
    # Create cluster expects cluster and returns pending operation.
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    # Get operation returns done operation.
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns expected cluster, populated with other fields by server.
    self.ExpectGetCluster(return_cluster)
    self.Run('{base} create {name} --quiet'.format(
        base=self.clusters_command_base.format(self.ZONE),
        name=self.CLUSTER_NAME))
    self.AssertErrContains(
        'Starting with version 1.18, clusters will have shielded GKE nodes by default.'
    )

  def testEnableSurgeUpgrade(self):
    cluster_kwargs = {}
    cluster_kwargs['nodePools'] = [
        self._MakeNodePool(
            upgradeSettings=self._MakeUpgradeSettings(
                maxSurge=3, maxUnavailable=2),
            name='default-pool')
    ]
    # Cluster create returns operation pending
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {name} --max-surge-upgrade=3 '
        '--max-unavailable-upgrade=2 --quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')


class CreateTestGAOnly(CreateTestGA):
  """gcloud GA track only using container v1 API (not beta/alpha)."""

  def testCreateAlphaClusterWithAutoUpgradeAutoRepairDisabled(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')
    cluster_kwargs = {'enableKubernetesAlpha': True, 'management': None}
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    return_args.update({
        'expireTime': base.format_date_time('P30D'),
    })
    self.ExpectGetCluster(
        self._RunningClusterForVersion('1.3.6', **cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --enable-kubernetes-alpha'.format(self.CLUSTER_NAME))
    c_config = c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                         self.PROJECT_ID)
    self._TestDefaultAuth(c_config)
    self.AssertErrContains('Created')
    self.AssertErrContains(
        'This will create a cluster with all Kubernetes Alpha features enabled')

  def testCreateEnableAddonsCloudRun(self):
    cluster_kwargs = {
        'addonsConfig':
            self.msgs.AddonsConfig(
                httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=False),
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=True),
                kubernetesDashboard=self.msgs.KubernetesDashboard(
                    disabled=False),
                networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                    disabled=True),
                cloudRunConfig=self.msgs.CloudRunConfig(disabled=False)),
        'loggingService':
            'logging.googleapis.com/kubernetes',
        'monitoringService':
            'monitoring.googleapis.com/kubernetes',
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.10.4'))
    self.Run((self.clusters_command_base.format(self.ZONE) + ' create {0}'
              ' --enable-stackdriver-kubernetes'
              ' --addons=HttpLoadBalancing,KubernetesDashboard,'
              'CloudRun').format(self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testCreateEnableAddonsCloudRunWithoutRequiredAddons(self):
    err_msg = (
        'The CloudRun-on-GKE addon (--addons=CloudRun) requires HTTP Load '
        'Balancing to be enabled via the --addons=HttpLoadBalancing flag.')
    with self.AssertRaisesExceptionMatches(c_util.Error, err_msg):
      self.Run((self.clusters_command_base.format(self.ZONE) +
                ' create {0} --enable-stackdriver-kubernetes '
                '--addons=CloudRun').format(self.CLUSTER_NAME))

  def testCreateAutoprovisioningUpgradeSettingsFromFile(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'rl-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(
                    upgradeSettings=m.UpgradeSettings(
                        maxSurge=1, maxUnavailable=2),
                    oauthScopes=[],
                ),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', minimum=1, maximum=2),
                    m.ResourceLimit(
                        resourceType='memory', minimum=10, maximum=20),
                ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    autoprovisioning_config = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
upgradeSettings:
  maxSurgeUpgrade: 1
  maxUnavailableUpgrade: 2
resourceLimits:
  - resourceType: 'cpu'
    minimum: 1
    maximum: 2
  - resourceType: 'memory'
    minimum: 10
    maximum: 20
        """)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--enable-autoprovisioning '
        '--autoprovisioning-config-file {}'.format(autoprovisioning_config))

  def testCreateAutoprovisioningUpgradeSettingsFromFlags(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'rl-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(
                    upgradeSettings=m.UpgradeSettings(
                        maxSurge=1, maxUnavailable=2),
                    oauthScopes=[],
                ),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', minimum=10, maximum=20),
                    m.ResourceLimit(
                        resourceType='memory', minimum=16, maximum=128)
                ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--enable-autoprovisioning --min-cpu 10 --max-cpu 20 '
        '--autoprovisioning-max-surge-upgrade=1 --autoprovisioning-max-unavailable-upgrade=2 '
        '--min-memory 16 --max-memory 128')

  def testCreateAutoprovisioningNodeManagementSettingsFromFile(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'rl-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(
                    management=m.NodeManagement(
                        autoRepair=False, autoUpgrade=True),
                    oauthScopes=[],
                ),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', minimum=1, maximum=2),
                    m.ResourceLimit(
                        resourceType='memory', minimum=10, maximum=20),
                ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    autoprovisioning_config = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
management:
  autoRepair: false
  autoUpgrade: true
resourceLimits:
  - resourceType: 'cpu'
    minimum: 1
    maximum: 2
  - resourceType: 'memory'
    minimum: 10
    maximum: 20
        """)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--enable-autoprovisioning '
        '--autoprovisioning-config-file {}'.format(autoprovisioning_config))

  def testCreateAutoprovisioningOnlyOneNodeManagementFromFileWithError(self):
    autoprovisioning_config_file = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
management:
  autoRepair: false
resourceLimits:
  - resourceType: 'cpu'
    minimum: 8
    maximum: 100
  - resourceType: 'memory'
    maximum: 20
        """)

    with self.assertRaises(c_util.Error):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' create my-cluster '
          ' --enable-autoprovisioning '
          '--autoprovisioning-config-file {}'.format(
              autoprovisioning_config_file))
    self.AssertErrContains(
        'Must specify both \'autoUpgrade\' and \'autoRepair\' in \'management\''
    )

  def testCreateAutoprovisioningOnlyOneUpgradeSettingsFromFileWithError(self):
    autoprovisioning_config_file = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
upgradeSettings:
  maxSurgeUpgrade: 1
resourceLimits:
  - resourceType: 'cpu'
    minimum: 8
    maximum: 100
  - resourceType: 'memory'
    maximum: 20
        """)

    with self.assertRaises(c_util.Error):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' create my-cluster '
          ' --enable-autoprovisioning '
          '--autoprovisioning-config-file {}'.format(
              autoprovisioning_config_file))
    self.AssertErrContains(
        'Must specify both \'maxSurgeUpgrade\' and \'maxUnavailableUpgrade\' in \'upgradeSettings\''
    )

  def testCreateAutoprovisioningNodeManagementFromFlags(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'rl-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(
                    management=m.NodeManagement(
                        autoRepair=False, autoUpgrade=True),
                    oauthScopes=[],
                ),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', minimum=10, maximum=20),
                    m.ResourceLimit(
                        resourceType='memory', minimum=16, maximum=128)
                ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--enable-autoprovisioning --min-cpu 10 --max-cpu 20 '
        '--no-enable-autoprovisioning-autorepair '
        '--enable-autoprovisioning-autoupgrade '
        '--min-memory 16 --max-memory 128')

  def testEnableAutoprovisioningWithFromFileWithError(self):
    autoprovisioning_config_file = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
minCpuPlatform: Skylake
resourceLimits:
  - resourceType: 'cpu'
    minimum: 8
    maximum: 100
  - resourceType: 'memory'
    maximum: 20
        """)
    with self.assertRaises(c_util.Error):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
          '--enable-autoprovisioning '
          '--autoprovisioning-config-file {}'.format(
              autoprovisioning_config_file))
    self.AssertErrContains('Min CPU platform not implemented in GA.')


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class CreateTestBeta(base.BetaTestBase, CreateTestGA):
  """gcloud Beta track using container v1beta1 API."""

  def testCreateWithLabels(self):
    cluster_kwargs = {
        'labels':
            self.msgs.Cluster.ResourceLabelsValue(
                additionalProperties=[
                    self.msgs.Cluster.ResourceLabelsValue.AdditionalProperty(
                        key='k', value='v'),
                    self.msgs.Cluster.ResourceLabelsValue.AdditionalProperty(
                        key='k2', value=''),
                ],),
    }

    # Cluster create returns operation pending
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs.copy()
    self.updateResponse(
        return_args, clusterApiVersion='0.18.2', currentMainVersion1='0.18.2')
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
            key='key1', value='val1', effect=effect_enum.NO_SCHEDULE),
        self.msgs.NodeTaint(
            key='key2', value='val2', effect=effect_enum.PREFER_NO_SCHEDULE),
        self.msgs.NodeTaint(
            key='key3', value='val3', effect=effect_enum.NO_EXECUTE)
    ]
    cluster_kwargs = {
        'nodeTaints': taints,
    }

    # Cluster create returns operation pending
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    return_args = cluster_kwargs.copy()
    self.updateResponse(
        return_args, clusterApiVersion='0.18.2', currentMainVersion1='0.18.2')
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --node-taints='
        'key1=val1:NoSchedule,key2=val2:PreferNoSchedule,key3=val3:NoExecute'
        .format(self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testCreateMinCpuPlatform(self):
    cluster_kwargs = {
        'minCpuPlatform': 'Skylake',
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.3.0'))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --min-cpu-platform=Skylake'.format(self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testCreateBetaFeatures(self):
    m = self.messages
    autoscaling_profiles_enum = (
        self.messages.ClusterAutoscaling.AutoscalingProfileValueValuesEnum)
    cluster_kwargs = {
        'name':
            'my-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(
                    serviceAccount='sa',
                    oauthScopes=['scope1', 'scope2'],
                ),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', maximum=10),
                    m.ResourceLimit(
                        resourceType='memory', maximum=64, minimum=8),
                    m.ResourceLimit(
                        resourceType='nvidia-tesla-k80', maximum=4, minimum=1),
                ],
                autoprovisioningLocations=['us-central1-a', 'us-central1-b'],
                autoscalingProfile=(
                    autoscaling_profiles_enum.OPTIMIZE_UTILIZATION)),
        'workloadMetadataConfig':
            m.WorkloadMetadataConfig(nodeMetadata=m.WorkloadMetadataConfig
                                     .NodeMetadataValueValuesEnum.SECURE),
        'verticalPodAutoscaling':
            m.VerticalPodAutoscaling(enabled=True),
        'bootDiskKmsKey':
            'projects/bing/locations/baz/keyRings/bar/cryptoKeys/foo',
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
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
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
        '--workload-metadata-from-node=secure '
        '--enable-autoprovisioning --max-cpu 10 --max-memory 64 --min-memory 8 '
        '--autoprovisioning-scopes=scope1,scope2 '
        '--autoprovisioning-service-account=sa '
        '--autoprovisioning-locations=us-central1-a,us-central1-b '
        '--max-accelerator type=nvidia-tesla-k80,count=4 '
        '--min-accelerator type=nvidia-tesla-k80,count=1 '
        '--enable-vertical-pod-autoscaling '
        '--boot-disk-kms-key {bootDiskKmsKey} '
        '--autoscaling-profile optimize-utilization '.format(**cluster_kwargs))
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
    kwargs = {
        'name': self.CLUSTER_NAME,
        'locations': locations,
    }
    # Cluster create returns operation pending
    self.ExpectCreateCluster(
        self._MakeCluster(**kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(
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
    cluster_kwargs = {'podSecurityPolicyConfig': psp_config}
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

  def testCreateNoEnableIpAlias(self):
    cluster_kwargs = {}
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    policy = self._MakeIPAllocationPolicy(useRoutes=True)
    expected_cluster.ipAllocationPolicy = policy
    # Cluster create returns operation pending
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--no-enable-ip-alias'.format(name=self.CLUSTER_NAME))

  def testCreateAllowRouteOverlap(self):
    cluster_kwargs = {
        'clusterIpv4Cidr': '10.1.0.0/16',
    }
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    policy = self._MakeIPAllocationPolicy(
        allowRouteOverlap=True, useRoutes=True)
    expected_cluster.ipAllocationPolicy = policy
    # Cluster create returns operation pending
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    # Get operation returns done
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns valid cluster
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--allow-route-overlap --cluster-ipv4-cidr=10.1.0.0/16 '
        '--no-enable-ip-alias'.format(name=self.CLUSTER_NAME))

  def testCreateAllowRouteOverlapWithIPAlias(self):
    cluster_kwargs = {}
    expected_cluster = self._MakeCluster(**cluster_kwargs)
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
       api_adapter.ALLOW_ROUTE_OVERLAP_WITHOUT_EXPLICIT_NETWORK_MODE),
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
    policy = self._MakeIPAllocationPolicy(
        createSubnetwork=False,
        useIpAliases=True,
    )
    expected_cluster.ipAllocationPolicy = policy
    config = self._MakePrivateClusterConfig(
        enablePrivateNodes=True, mainIpv4Cidr='172.16.10.0/28')
    expected_cluster.privateClusterConfig = config
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)

    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-ip-alias '
        '--private-cluster '
        '--main-ipv4-cidr=172.16.10.0/28 '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  @parameterized.parameters(
      (' --enable-main-global-access ', True),
      (' --no-enable-main-global-access ', False),
  )
  def testEnableMainGlobalAccess(self, flags, enabled):
    cluster_kwargs = {
        'name': self.CLUSTER_NAME,
    }

    expected_cluster = self._MakeCluster(**cluster_kwargs)
    policy = self._MakeIPAllocationPolicy(
        createSubnetwork=False,
        useIpAliases=True,
    )
    expected_cluster.ipAllocationPolicy = policy
    main_global_access_config = self.msgs.PrivateClusterMainGlobalAccessConfig(
        enabled=enabled)
    config = self._MakePrivateClusterConfig(
        mainGlobalAccessConfig=main_global_access_config,
        enablePrivateNodes=True,
        mainIpv4Cidr='172.16.10.0/28')
    expected_cluster.privateClusterConfig = config
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)

    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-ip-alias '
        '--private-cluster '
        '--main-ipv4-cidr=172.16.10.0/28 '
        '{flags}'
        '--quiet'.format(name=self.CLUSTER_NAME, flags=flags))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testEnableIntraNodeVisibility(self):
    cluster_kwargs = {
        'enableIntraNodeVisibility': True,
    }
    # Cluster create returns operation pending
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    expected_cluster.networkConfig = self.messages.NetworkConfig(
        enableIntraNodeVisibility=True)
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
        '--enable-intra-node-visibility '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testCreateEnableAddonsIstio(self):
    mtls = self.messages.IstioConfig.AuthValueValuesEnum.AUTH_MUTUAL_TLS
    cluster_kwargs = {
        'addonsConfig':
            self.msgs.AddonsConfig(
                httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=False),
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=True),
                kubernetesDashboard=self.msgs.KubernetesDashboard(
                    disabled=False),
                networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                    disabled=True),
                istioConfig=self.msgs.IstioConfig(disabled=False, auth=mtls)),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.7.0'))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --addons=HttpLoadBalancing,KubernetesDashboard,Istio'
        ' --istio-config=auth=mtls_strict'.format(self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testCreateEnableAddonsIstioNoAuth(self):
    auth = self.messages.IstioConfig.AuthValueValuesEnum.AUTH_NONE
    cluster_kwargs = {
        'addonsConfig':
            self.msgs.AddonsConfig(
                httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=False),
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=True),
                kubernetesDashboard=self.msgs.KubernetesDashboard(
                    disabled=False),
                networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                    disabled=True),
                istioConfig=self.msgs.IstioConfig(disabled=False, auth=auth)),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.7.0'))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --addons=HttpLoadBalancing,KubernetesDashboard,Istio'
        .format(self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testCreateAutoprovisioningMinCpuPlatformFromFile(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'rl-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(
                    minCpuPlatform='Skylake',
                    oauthScopes=[],
                ),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', minimum=1, maximum=2),
                    m.ResourceLimit(
                        resourceType='memory', minimum=10, maximum=20),
                ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    autoprovisioning_config = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
minCpuPlatform: Skylake
resourceLimits:
  - resourceType: 'cpu'
    minimum: 1
    maximum: 2
  - resourceType: 'memory'
    minimum: 10
    maximum: 20
        """)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--enable-autoprovisioning '
        '--autoprovisioning-config-file {}'.format(autoprovisioning_config))

  def testCreateAutoprovisioningUpgradeSettingsFromFile(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'rl-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(
                    upgradeSettings=m.UpgradeSettings(
                        maxSurge=1, maxUnavailable=2),
                    oauthScopes=[],
                ),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', minimum=1, maximum=2),
                    m.ResourceLimit(
                        resourceType='memory', minimum=10, maximum=20),
                ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    autoprovisioning_config = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
upgradeSettings:
  maxSurgeUpgrade: 1
  maxUnavailableUpgrade: 2
resourceLimits:
  - resourceType: 'cpu'
    minimum: 1
    maximum: 2
  - resourceType: 'memory'
    minimum: 10
    maximum: 20
        """)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--enable-autoprovisioning '
        '--autoprovisioning-config-file {}'.format(autoprovisioning_config))

  def testCreateAutoprovisioningUpgradeSettingsFromFlags(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'rl-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(
                    upgradeSettings=m.UpgradeSettings(
                        maxSurge=1, maxUnavailable=2),
                    oauthScopes=[],
                ),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', minimum=10, maximum=20),
                    m.ResourceLimit(
                        resourceType='memory', minimum=16, maximum=128)
                ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--enable-autoprovisioning --min-cpu 10 --max-cpu 20 '
        '--autoprovisioning-max-surge-upgrade=1 --autoprovisioning-max-unavailable-upgrade=2 '
        '--min-memory 16 --max-memory 128')

  def testCreateAutoprovisioningNodeManagementSettingsFromFile(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'rl-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(
                    management=m.NodeManagement(
                        autoRepair=False, autoUpgrade=True),
                    oauthScopes=[],
                ),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', minimum=1, maximum=2),
                    m.ResourceLimit(
                        resourceType='memory', minimum=10, maximum=20),
                ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    autoprovisioning_config = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
management:
  autoRepair: false
  autoUpgrade: true
resourceLimits:
  - resourceType: 'cpu'
    minimum: 1
    maximum: 2
  - resourceType: 'memory'
    minimum: 10
    maximum: 20
        """)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--enable-autoprovisioning '
        '--autoprovisioning-config-file {}'.format(autoprovisioning_config))

  def testCreateAutoprovisioningOnlyOneNodeManagementFromFileWithError(self):
    autoprovisioning_config_file = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
management:
  autoRepair: false
resourceLimits:
  - resourceType: 'cpu'
    minimum: 8
    maximum: 100
  - resourceType: 'memory'
    maximum: 20
        """)

    with self.assertRaises(c_util.Error):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' create my-cluster '
          ' --enable-autoprovisioning '
          '--autoprovisioning-config-file {}'.format(
              autoprovisioning_config_file))
    self.AssertErrContains(
        'Must specify both \'autoUpgrade\' and \'autoRepair\' in \'management\''
    )

  def testCreateAutoprovisioningOnlyOneUpgradeSettingsFromFileWithError(self):
    autoprovisioning_config_file = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
upgradeSettings:
  maxSurgeUpgrade: 1
resourceLimits:
  - resourceType: 'cpu'
    minimum: 8
    maximum: 100
  - resourceType: 'memory'
    maximum: 20
        """)

    with self.assertRaises(c_util.Error):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' create my-cluster '
          ' --enable-autoprovisioning '
          '--autoprovisioning-config-file {}'.format(
              autoprovisioning_config_file))
    self.AssertErrContains(
        'Must specify both \'maxSurgeUpgrade\' and \'maxUnavailableUpgrade\' in \'upgradeSettings\''
    )

  def testCreateAutoprovisioningNodeManagementFromFlags(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'rl-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(
                    management=m.NodeManagement(
                        autoRepair=False, autoUpgrade=True),
                    oauthScopes=[],
                ),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', minimum=10, maximum=20),
                    m.ResourceLimit(
                        resourceType='memory', minimum=16, maximum=128)
                ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--enable-autoprovisioning --min-cpu 10 --max-cpu 20 '
        '--no-enable-autoprovisioning-autorepair '
        '--enable-autoprovisioning-autoupgrade '
        '--min-memory 16 --max-memory 128')

  def testCreateAutoprovisioningMinCpuPlatformFromFlags(self):
    m = self.messages
    cluster_kwargs = {
        'name':
            'rl-cluster',
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                enableNodeAutoprovisioning=True,
                autoprovisioningNodePoolDefaults=m
                .AutoprovisioningNodePoolDefaults(
                    minCpuPlatform='Skylake',
                    oauthScopes=[],
                ),
                resourceLimits=[
                    m.ResourceLimit(resourceType='cpu', minimum=10, maximum=20),
                    m.ResourceLimit(
                        resourceType='memory', minimum=16, maximum=128)
                ]),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create rl-cluster '
        '--enable-autoprovisioning --min-cpu 10 --max-cpu 20 '
        '--autoprovisioning-min-cpu-platform Skylake '
        '--min-memory 16 --max-memory 128')

  def testCreateDisableAddonsIstio(self):
    cluster_kwargs = {
        'addonsConfig':
            self.msgs.AddonsConfig(
                httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=False),
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=True),
                kubernetesDashboard=self.msgs.KubernetesDashboard(
                    disabled=False),
                networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                    disabled=True)),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.7.0'))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --addons=HttpLoadBalancing,KubernetesDashboard'.format(
            self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testCreateValidateAddonsIstioConfig(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --addons=HttpLoadBalancing,KubernetesDashboard,Istio'
          ' --istio-config=auth=mtl_strict'.format(self.CLUSTER_NAME))
    self.AssertErrContains('auth is either MTLS_PERMISSIVE or MTLS_STRICT')

  def testCreateValidateAddonsIstio(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --addons=HttpLoadBalancing,KubernetesDashboard'
          ' --istio-config=auth=mtls_strict'.format(self.CLUSTER_NAME))
    self.AssertErrContains('--addon=Istio must be specified')

  def testCreateEnableAddonsCloudRun(self):
    auth = self.messages.IstioConfig.AuthValueValuesEnum.AUTH_NONE
    cluster_kwargs = {
        'addonsConfig':
            self.msgs.AddonsConfig(
                httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=False),
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=True),
                kubernetesDashboard=self.msgs.KubernetesDashboard(
                    disabled=False),
                networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                    disabled=True),
                cloudRunConfig=self.msgs.CloudRunConfig(disabled=False),
                istioConfig=self.msgs.IstioConfig(disabled=False, auth=auth)),
        'clusterTelemetry':
            self.msgs.ClusterTelemetry(
                type=self.msgs.ClusterTelemetry.TypeValueValuesEnum.ENABLED),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.10.4'))
    self.Run((self.clusters_command_base.format(self.ZONE) + ' create {0}'
              ' --enable-stackdriver-kubernetes'
              ' --addons=HttpLoadBalancing,KubernetesDashboard,'
              'Istio,CloudRun').format(self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testCreateEnableAddonsCloudRunWithoutStackdriverKubeneters(self):
    err_msg = """\
The CloudRun-on-GKE addon (--addons=CloudRun) requires Cloud Logging and Cloud \
Monitoring to be enabled via the --enable-stackdriver-kubernetes flag."""
    with self.AssertRaisesExceptionMatches(c_util.Error, err_msg):
      self.Run((self.clusters_command_base.format(self.ZONE) +
                ' create {0} --addons=CloudRun').format(self.CLUSTER_NAME))

  @parameterized.named_parameters(
      ('HTTPLoadBalancingDisabled', 'HTTP Load Balancing', 'HttpLoadBalancing'))
  def testCreateEnableAddonsCloudRunWithoutRequiredAddons(self, fname, aname):
    err_msg = ('The CloudRun-on-GKE addon (--addons=CloudRun) requires %s to '
               'be enabled via the --addons=%s flag.' % (fname, aname))
    with self.AssertRaisesExceptionMatches(c_util.Error, err_msg):
      addons = ['HttpLoadBalancing', 'CloudRun']
      addons.remove(aname)
      self.Run((self.clusters_command_base.format(self.ZONE) +
                ' create {0} --enable-stackdriver-kubernetes '
                '--addons={1}').format(self.CLUSTER_NAME, ','.join(addons)))

  def testCreateEnableAddonsNodeLocalDNS(self):
    cluster_kwargs = {
        'addonsConfig':
            self.msgs.AddonsConfig(
                httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=True),
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=True),
                kubernetesDashboard=self.msgs.KubernetesDashboard(
                    disabled=True),
                networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                    disabled=True),
                dnsCacheConfig=self.msgs.DnsCacheConfig(enabled=True)),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.13.3'))

    self.Run((self.clusters_command_base.format(self.ZONE) + ' create {0} '
              ' --addons=NodeLocalDNS --quiet').format(self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testCreateEnableAddonsConfigConnector(self):
    cluster_kwargs = {
        'addonsConfig':
            self.msgs.AddonsConfig(
                httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=True),
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=True),
                kubernetesDashboard=self.msgs.KubernetesDashboard(
                    disabled=True),
                networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                    disabled=True),
                configConnectorConfig=self.msgs.ConfigConnectorConfig(
                    enabled=True)),
        'clusterTelemetry':
            self.msgs.ClusterTelemetry(
                type=self.msgs.ClusterTelemetry.TypeValueValuesEnum.ENABLED),
    }

    cluster = self._MakeCluster(**cluster_kwargs)
    cluster.workloadIdentityConfig = self.messages.WorkloadIdentityConfig(
        workloadPool='{}.svc.id.goog'.format(self.PROJECT_ID))
    self.ExpectCreateCluster(cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.15.11-gke.5'))

    self.Run(
        (self.clusters_command_base.format(self.ZONE) + ' create {cluster} '
         ' --enable-stackdriver-kubernetes'
         ' --workload-pool={project}.svc.id.goog'
         ' --addons=ConfigConnector --quiet').format(
             cluster=self.CLUSTER_NAME, project=self.PROJECT_ID))
    self.AssertOutputContains('RUNNING')

  def testCreateEnableAddonsConfigConnectorWithoutStackdriverKubernetes(self):
    logging = 'Cloud Logging'
    monitoring = 'Cloud Monitoring'
    err_msg = (
        'The ConfigConnector-on-GKE addon (--addons=ConfigConnector) requires '
        '%s and %s to be enabled via the --enable-stackdriver-kubernetes flag.'
    ) % (logging, monitoring)
    with self.AssertRaisesExceptionMatches(c_util.Error, err_msg):
      self.Run(
          (self.clusters_command_base.format(self.ZONE) +
           ' create {0} --addons=ConfigConnector').format(self.CLUSTER_NAME))

  def testCreateEnableAddonsConfigConnectorWithoutWorkloadIdentity(self):
    err_msg = ('The ConfigConnector-on-GKE addon (--addons=ConfigConnector) '
               'requires workload identity to be enabled via the '
               '--workload-pool=WORKLOAD_POOL flag.')
    with self.AssertRaisesExceptionMatches(c_util.Error, err_msg):
      self.Run((
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --addons=ConfigConnector --enable-stackdriver-kubernetes'
      ).format(self.CLUSTER_NAME))

  def testCreateEnableAddonsApplicationManager(self):
    cluster_kwargs = {
        'addonsConfig':
            self.msgs.AddonsConfig(
                httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=True),
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=True),
                kubernetesDashboard=self.msgs.KubernetesDashboard(
                    disabled=True),
                networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                    disabled=True),
                kalmConfig=self.msgs.KalmConfig(enabled=True)),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.15.4'))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --addons=ApplicationManager --quiet'.format(
            self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testWorkloadIdentityConfigLegacy(self):
    expected_cluster, return_cluster = self.makeExpectedAndReturnClusters({})
    expected_cluster.workloadIdentityConfig = self.messages.WorkloadIdentityConfig(
        identityNamespace='{}.svc.id.goog'.format(self.PROJECT_ID))
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(return_cluster)
    self.Run('{base} create {name} --identity-namespace={project}.svc.id.goog'
             .format(
                 base=self.clusters_command_base.format(self.ZONE),
                 name=self.CLUSTER_NAME,
                 project=self.PROJECT_ID))
    self.AssertOutputContains('RUNNING')

  def testWarnNodeVersionWithAutoUpgradeEnabled(self):
    cluster_kwargs = {
        'nodeVersion':
            self.VERSION,
        'management':
            self.messages.NodeManagement(autoRepair=True, autoUpgrade=True)
    }
    expected_cluster, return_cluster = self.makeExpectedAndReturnClusters(
        cluster_kwargs)
    # Create cluster expects cluster and returns pending operation.
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    # Get operation returns done operation.
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    # Get returns expected cluster, populated with other fields by server.
    self.ExpectGetCluster(return_cluster)
    self.Run('{base} create {name} --node-version {version} --quiet'.format(
        base=self.clusters_command_base.format(self.ZONE),
        name=self.CLUSTER_NAME,
        version=self.VERSION))
    self.AssertErrContains(c_util.WARN_NODE_VERSION_WITH_AUTOUPGRADE_ENABLED)

  def testEnableDatabaseEncryption(self):
    cluster_kwargs = {
        'databaseEncryptionKey':
            'projects/p/locations/l/keyRings/kr/cryptoKeys/k',
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--database-encryption-key=projects/p/locations/l/keyRings/kr/cryptoKeys/k'
        .format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testInvalidDatabaseEncryptionKey(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' create {name} '
          '--database-encryption-key=projects/p'.format(name=self.CLUSTER_NAME))
    self.AssertErrContains(
        'Must be in format of \'projects/[KEY_PROJECT_ID]/locations/[LOCATION]/keyRings/[RING_NAME]/cryptoKeys/[KEY_NAME]\''
    )

  @parameterized.parameters(('rapid'), ('regular'), ('stable'))
  def testReleaseChannelRapid(self, channel):
    channels = {
        'rapid': self.messages.ReleaseChannel.ChannelValueValuesEnum.RAPID,
        'regular': self.messages.ReleaseChannel.ChannelValueValuesEnum.REGULAR,
        'stable': self.messages.ReleaseChannel.ChannelValueValuesEnum.STABLE,
    }
    cluster_kwargs = {
        'releaseChannel':
            self.messages.ReleaseChannel(channel=channels[channel]),
    }

    expected_cluster = self._MakeCluster(**cluster_kwargs)
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)

    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--release-channel={rc} '
        '--quiet'.format(name=self.CLUSTER_NAME, rc=channel))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  @parameterized.parameters(('--cluster-version=1.7.1'),
                            ('--node-version=1.7.1'))
  def testReleaseChannelConflictingFlagsError(self, flag):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' create {name} '
          '--release-channel=rapid '
          '{flag}'.format(name=self.CLUSTER_NAME, flag=flag))
    self.AssertErrContains('At most one of')

  def testNodeVersionClusterVersionNoError(self):
    cluster_kwargs = {
        'clusterApiVersion': '1.7.1',
        'nodeVersion': '1.7.1',
    }
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)

    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--cluster-version=1.7.1 '
        '--node-version=1.7.1 '.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  @parameterized.parameters(('invalid'), ('Rapid'), ('RAPID'), ('Regular'),
                            ('REGULAR'), ('Stable'), ('STABLE'))
  def testReleaseChannelInvalidChannelError(self, channel_name):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' create {name} '
          '--release-channel={channel}'.format(
              name=self.CLUSTER_NAME, channel=channel_name))
    self.AssertErrContains('Invalid choice')

  @parameterized.parameters('--max-surge-upgrade=2',
                            '--max-unavailable-upgrade=1')
  def testInvalidSurgeUpgrade(self, upgrade_flag):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {name} {upgrade_flag} --quiet'.format(
              name=self.CLUSTER_NAME, upgrade_flag=upgrade_flag))
    self.AssertErrContains(c_util.INVALIID_SURGE_UPGRADE_SETTINGS)

  def testCreateEnableAddonsGcePersistentDiskCsiDriverConfig(self):
    cluster_kwargs = {
        'addonsConfig':
            self.msgs.AddonsConfig(
                httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=True),
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=True),
                kubernetesDashboard=self.msgs.KubernetesDashboard(
                    disabled=True),
                networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                    disabled=True),
                gcePersistentDiskCsiDriverConfig=\
                self.msgs.GcePersistentDiskCsiDriverConfig(
                    enabled=True)),
    }
    cluster = self._MakeCluster(**cluster_kwargs)
    self.ExpectCreateCluster(cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.14.3'))

    self.Run((self.clusters_command_base.format(self.ZONE) + ' create {0} '
              ' --addons=GcePersistentDiskCsiDriver --quiet').format(
                  self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testCreateNoDefaults(self):
    cluster_kwargs = {
        'clusterTelemetry':
            self.msgs.ClusterTelemetry(
                type=self.msgs.ClusterTelemetry.TypeValueValuesEnum.DISABLED),
        'loggingService':
            None,
        'monitoringService':
            None,
    }
    CreateTestGA.testCreateNoDefaults(self, cluster_kwargs)

  def testEnableStackdriverKubernetes(self):
    cluster_kwargs = {
        'clusterTelemetry':
            self.msgs.ClusterTelemetry(
                type=self.msgs.ClusterTelemetry.TypeValueValuesEnum.ENABLED),
    }
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
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-stackdriver-kubernetes '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testEnableLoggingMonitoringSystemOnly(self):
    cluster_kwargs = {
        'clusterTelemetry':
            self.msgs.ClusterTelemetry(
                type=self.msgs.ClusterTelemetry.TypeValueValuesEnum.SYSTEM_ONLY
            ),
    }
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-logging-monitoring-system-only '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testEnableGvnic(self):
    cluster_kwargs = {
        'enableGvnic': True,
    }
    # Cluster create returns operation pending
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    expected_cluster.enableGvnic = True
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
        '--enable-gvnic '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')


# Mixin class must come in first to have the correct multi-inheritance behavior.
class CreateTestAlpha(base.AlphaTestBase, CreateTestBeta):
  """gcloud Alpha track using container v1alpha1 API."""

  def testCreateAlphaFeatures(self):
    m = self.messages
    format_enum = self.messages.LocalSsdVolumeConfig.FormatValueValuesEnum
    autoscaling_profiles_enum = \
        self.messages.ClusterAutoscaling.AutoscalingProfileValueValuesEnum
    cluster_kwargs = {
        'name':
            'my-cluster',
        'workloadMetadataConfig':
            m.WorkloadMetadataConfig(nodeMetadata=m.WorkloadMetadataConfig
                                     .NodeMetadataValueValuesEnum.SECURE),
        'localSsdVolumeConfigs': [
            m.LocalSsdVolumeConfig(count=2, type='nvme', format=format_enum.FS),
            m.LocalSsdVolumeConfig(
                count=1, type='scsi', format=format_enum.BLOCK),
        ],
        'clusterAutoscaling':
            m.ClusterAutoscaling(
                autoscalingProfile=\
                  autoscaling_profiles_enum.OPTIMIZE_UTILIZATION),
        'bootDiskKmsKey':
            'projects/bing/locations/baz/keyRings/bar/cryptoKeys/foo',
    }
    cluster_kwargs['nodePools'] = [
        self._MakeDefaultNodePool(
            nodePoolName='default-pool', initialNodeCount=500, **cluster_kwargs)
    ]
    # Cluster create returns operation pending
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs),
        self._MakeOperation(
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
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
        self.clusters_command_base.format(self.ZONE) + ' create my-cluster '
        '--num-nodes=500 '
        '--workload-metadata-from-node=secure '
        '--local-ssd-volumes count=2,type=nvme,format=fs '
        '--local-ssd-volumes count=1,type=scsi,format=block '
        '--boot-disk-kms-key={bootDiskKmsKey} '
        '--autoscaling-profile optimize-utilization '.format(**cluster_kwargs))
    self.AssertOutputMatches(
        (r'NAME LOCATION MASTER_VERSION MASTER_IP MACHINE_TYPE NODE_VERSION '
         'NUM_NODES STATUS\n'
         '{name} {zone} {endpoint} '
         '{num_nodes} {status}\\n').format(
             name=return_cluster.name,
             num_nodes=return_cluster.currentNodeCount,
             zone=return_cluster.zone,
             endpoint=return_cluster.endpoint,
             status=return_cluster.status,
         ),
        normalize_space=True)

  def testEnableSharedNetwork(self):
    cluster_kwargs = {'subnetwork': 'my-subnetwork', 'management': None}

    policy = self._MakeIPAllocationPolicy(
        useIpAliases=True,
        createSubnetwork=False,
        servicesSecondaryRangeName='services-range',
        clusterSecondaryRangeName='cluster-range',
    )
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    expected_cluster.ipAllocationPolicy = policy
    expected_cluster.enableKubernetesAlpha = True
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(
        return_args,
        enableKubernetesAlpha=True,
        ipAllocationPolicy=policy,
        subnetwork=cluster_kwargs['subnetwork'])
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)

    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-kubernetes-alpha '
        '--enable-ip-alias '
        '--subnetwork my-subnetwork '
        '--cluster-secondary-range-name cluster-range '
        '--services-secondary-range-name services-range '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

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
            targetLink=self.TARGET_LINK.format(self.API_VERSION,
                                               self.PROJECT_NUM, self.ZONE,
                                               cluster_kwargs['name'])))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create localssdvolumeconfig-cluster '
        '--local-ssd-volumes count=1,type="scsi",format="fs"')

  @parameterized.parameters((1, 'notatype', 'fs'), (4, 'scsi', 'notaformat'),
                            ('notacount', 'scsi', 'fs'), (0, 'scsi', 'fs'))
  def testCreateInvalidLocalSsdVolumeConfig(self, ssd_count, ssd_type,
                                            ssd_format):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --local-ssd-volumes count={1},type={2},format={3}'
          .format(self.CLUSTER_NAME, ssd_count, ssd_type, ssd_format))
    self.AssertErrContains('argument --local-ssd-volumes')

  def testCreateEmptyLocalSsdVolumeConfig(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' create {0} --local-ssd-volumes'.format(self.CLUSTER_NAME))
    self.AssertErrContains('argument --local-ssd-volumes')

  def testCreateEnableAddonsCloudRun(self):
    auth = self.messages.IstioConfig.AuthValueValuesEnum.AUTH_NONE
    cluster_kwargs = {
        'addonsConfig':
            self.msgs.AddonsConfig(
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=True),
                httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=False),
                kubernetesDashboard=self.msgs.KubernetesDashboard(
                    disabled=False),
                networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                    disabled=True),
                cloudRunConfig=self.msgs.CloudRunConfig(
                    disabled=False, enableAlphaFeatures=False),
                istioConfig=self.msgs.IstioConfig(disabled=False, auth=auth)),
        'clusterTelemetry':
            self.msgs.ClusterTelemetry(
                type=self.msgs.ClusterTelemetry.TypeValueValuesEnum.ENABLED),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.10.4'))
    self.Run((self.clusters_command_base.format(self.ZONE) + ' create {0}'
              ' --enable-stackdriver-kubernetes'
              ' --addons=HttpLoadBalancing,KubernetesDashboard,'
              'Istio,CloudRun').format(self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testCreateEnableAddonsCloudRunAlphaFeatures(self):
    auth = self.messages.IstioConfig.AuthValueValuesEnum.AUTH_NONE
    cluster_kwargs = {
        'addonsConfig':
            self.msgs.AddonsConfig(
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=True),
                httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=False),
                kubernetesDashboard=self.msgs.KubernetesDashboard(
                    disabled=False),
                networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                    disabled=True),
                cloudRunConfig=self.msgs.CloudRunConfig(
                    disabled=False, enableAlphaFeatures=True),
                istioConfig=self.msgs.IstioConfig(disabled=False, auth=auth)),
        'clusterTelemetry':
            self.msgs.ClusterTelemetry(
                type=self.msgs.ClusterTelemetry.TypeValueValuesEnum.ENABLED),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.10.4'))
    self.Run((self.clusters_command_base.format(self.ZONE) + ' create {0}'
              ' --enable-stackdriver-kubernetes --enable-cloud-run-alpha'
              ' --addons=HttpLoadBalancing,KubernetesDashboard,'
              'Istio,CloudRun').format(self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testCreateEnableAddonsCloudBuild(self):
    cluster_kwargs = {
        'addonsConfig':
            self.msgs.AddonsConfig(
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=True),
                networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                    disabled=True),
                httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=True),
                kubernetesDashboard=self.msgs.KubernetesDashboard(
                    disabled=True,),
                cloudBuildConfig=self.msgs.CloudBuildConfig(enabled=True)),
        'clusterTelemetry':
            self.msgs.ClusterTelemetry(
                type=self.msgs.ClusterTelemetry.TypeValueValuesEnum.ENABLED),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.14.2'))
    self.Run((self.clusters_command_base.format(self.ZONE) + ' create {0}'
              ' --addons=CloudBuild --enable-stackdriver-kubernetes').format(
                  self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testCreateEnableAddonsCloudBuildWithoutStackdriverKubeneters(self):
    err_msg = """\
Cloud Build for Anthos (--addons=CloudBuild) requires Cloud Logging and Cloud Monitoring to be enabled via the --enable-stackdriver-kubernetes flag.
"""
    with self.AssertRaisesExceptionMatches(c_util.Error, err_msg):
      self.Run((self.clusters_command_base.format(self.ZONE) +
                ' create {0} --addons=CloudBuild').format(self.CLUSTER_NAME))

  @parameterized.parameters(
      ('--node-pool-name=some-node-pool', 'some-node-pool'),
      (None, 'default-pool'),
  )
  def testNodePoolNameForSinglePool(self, param, expected):
    cluster_kwargs = {}
    cmd = '{base} create {name}'.format(
        base=self.clusters_command_base.format(self.ZONE),
        name=self.CLUSTER_NAME)
    if param is not None:
      cmd = '{cmd} {param}'.format(cmd=cmd, param=param)

    cluster_kwargs['nodePools'] = [
        self._MakeDefaultNodePool(
            nodePoolName=expected, initialNodeCount=1, **cluster_kwargs)
    ]
    expected_cluster, return_cluster = self.makeExpectedAndReturnClusters(
        cluster_kwargs)
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(return_cluster)

    self.Run(cmd + ' --num-nodes=1')
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  @parameterized.parameters(
      ('--node-pool-name=some-node-pool', 'some-node-pool'),
      (None, 'default-pool'),
  )
  def testNodePoolNameForMultiplePools(self, param, expected):
    cluster_kwargs = {}
    cmd = '{base} create {name}'.format(
        base=self.clusters_command_base.format(self.ZONE),
        name=self.CLUSTER_NAME)
    if param is not None:
      cmd = '{cmd} {param}'.format(cmd=cmd, param=param)

    def n(pool_index):
      return self._MakeDefaultNodePool(
          nodePoolName='{expected}-{pool}'.format(
              expected=expected, pool=pool_index),
          initialNodeCount=500 if pool_index < 3 else 499,
          **cluster_kwargs)

    # Expect 1999 nodes in four pools (500 + 500 + 500 + 499)
    cluster_kwargs['nodePools'] = [n(pool_index) for pool_index in range(4)]
    expected_cluster, return_cluster = self.makeExpectedAndReturnClusters(
        cluster_kwargs)
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(return_cluster)

    # Create 500 node pools with 1999 nodes - 500 - 500 - 500 - 499
    self.Run(cmd + ' --num-nodes=1999 --max-nodes-per-pool=500')
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testEnableAuthenticatorSecurityGroups(self):
    cluster_kwargs = {'enableKubernetesAlpha': True, 'management': None}
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    expected_cluster.authenticatorGroupsConfig = (
        self.messages.AuthenticatorGroupsConfig(
            enabled=True, securityGroup='AdminPeople'))
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)

    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-kubernetes-alpha '
        '--security-group=AdminPeople '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testEnableAuthenticatorSecurityGroupsBeta(self):
    cluster_kwargs = {}
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    expected_cluster.authenticatorGroupsConfig = (
        self.messages.AuthenticatorGroupsConfig(
            enabled=True, securityGroup='AdminPeople'))
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)

    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--security-group=AdminPeople '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  @parameterized.parameters(
      ('--security-profile=test-profile-1', 'test-profile-1', False),
      ('--security-profile=test-profile-1 --security-profile-runtime-rules',
       'test-profile-1', False),
      ('--security-profile=test-profile-1 --no-security-profile-runtime-rules',
       'test-profile-1', True),
      ('', None, None),
  )
  def testSecurityProfile(self, flags, expect_profile,
                          expect_disable_runtime_rules):
    cluster_kwargs = {}
    expected_cluster, return_cluster = self.makeExpectedAndReturnClusters(
        cluster_kwargs)
    if expect_profile is not None:
      expected_cluster.securityProfile = self.messages.SecurityProfile(
          name=expect_profile, disableRuntimeRules=expect_disable_runtime_rules)
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(return_cluster)
    self.Run('{base} create {name} {flags} --quiet'.format(
        base=self.clusters_command_base.format(self.ZONE),
        name=self.CLUSTER_NAME,
        flags=flags))

  def testEnableTpuServiceNetworking(self):
    cluster_kwargs = {
        'enableTpu': True,
    }
    # Cluster create returns operation pending
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    policy = self._MakeIPAllocationPolicy(
        useIpAliases=True,
        createSubnetwork=False,
        tpuUseServiceNetworking=None,
    )
    expected_cluster.ipAllocationPolicy = policy
    tpu_config = self._MakeTpuConfig(
        enabled=True, ipv4CidrBlock=None, useServiceNetworking=True)
    expected_cluster.tpuConfig = tpu_config
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
        '--enable-ip-alias '
        '--enable-tpu '
        '--enable-tpu-service-networking '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  @parameterized.parameters(
      ('--enable-ip-alias --enable-tpu-service-networking', c_util.Error,
       api_adapter.PREREQUISITE_OPTION_ERROR_MSG.format(
           prerequisite='enable-tpu', opt='enable-tpu-service-networking')),
      ('--enable-ip-alias --enable-tpu --tpu-ipv4-cidr=10.1.0.0/20 '
       '--enable-tpu-service-networking', cli_test_base.MockArgumentError,
       'At most one of --enable-tpu-service-networking | '
       '--tpu-ipv4-cidr may be specified'),
  )
  def testEnableTpuBadArgs(self, flags, expected_err, expected_msg):
    command = (
        self.clusters_command_base.format(self.ZONE) +
        ' create {name} --quiet '.format(name=self.CLUSTER_NAME) + flags)
    self.AssertRaisesExceptionMatches(expected_err, expected_msg, self.Run,
                                      command)

  def testEnablePrivateIPv6Access(self):
    cluster_kwargs = {'enableKubernetesAlpha': True, 'management': None}
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    expected_cluster.networkConfig = (
        self.messages.NetworkConfig(enablePrivateIpv6Access=True))
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)

    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-kubernetes-alpha '
        '--enable-private-ipv6-access '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testCreateEnableAddonsNodeLocalDNS(self):
    cluster_kwargs = {
        'addonsConfig':
            self.msgs.AddonsConfig(
                httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=True),
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=True),
                kubernetesDashboard=self.msgs.KubernetesDashboard(
                    disabled=True),
                networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                    disabled=True),
                dnsCacheConfig=self.msgs.DnsCacheConfig(enabled=True)),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.13.3'))

    self.Run((self.clusters_command_base.format(self.ZONE) + ' create {0} '
              ' --addons=NodeLocalDNS --quiet').format(self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testCreateEnableAddonsApplicationManager(self):
    cluster_kwargs = {
        'addonsConfig':
            self.msgs.AddonsConfig(
                httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=True),
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=True),
                kubernetesDashboard=self.msgs.KubernetesDashboard(
                    disabled=True),
                networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                    disabled=True),
                kalmConfig=self.msgs.KalmConfig(enabled=True)),
    }
    self.ExpectCreateCluster(
        self._MakeCluster(**cluster_kwargs), self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(self._RunningClusterForVersion('1.15.4'))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' create {0} --addons=ApplicationManager --quiet'.format(
            self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')

  def testLinuxSysctlConfig(self):
    cluster_kwargs = {
        'linuxNodeConfig':
            self.msgs.LinuxNodeConfig(
                sysctls=self.msgs.LinuxNodeConfig
                .SysctlsValue(additionalProperties=[
                    self.msgs.LinuxNodeConfig.SysctlsValue.AdditionalProperty(
                        key='net.core.somaxconn', value='1024'),
                    self.msgs.LinuxNodeConfig.SysctlsValue.AdditionalProperty(
                        key='net.ipv4.tcp_rmem', value='4096 87380 6291456'),
                ])),
    }
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--linux-sysctls="net.core.somaxconn=1024,'
        'net.ipv4.tcp_rmem=4096 87380 6291456" '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testDisableDefaultSnat(self):
    cluster_kwargs = {}
    # Cluster create returns operation pending
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    policy = self._MakeIPAllocationPolicy(
        clusterIpv4Cidr=None, createSubnetwork=False, useIpAliases=True)
    expected_cluster.ipAllocationPolicy = policy
    config = self._MakePrivateClusterConfig(
        enablePrivateNodes=True, mainIpv4Cidr='172.16.10.0/28')
    expected_cluster.privateClusterConfig = config
    default_snat_status = self.msgs.DefaultSnatStatus(
        disabled=True)
    expected_cluster.networkConfig = self.msgs.NetworkConfig(
        defaultSnatStatus=default_snat_status)
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
        '--enable-ip-alias '
        '--enable-private-nodes '
        '--main-ipv4-cidr=172.16.10.0/28 '
        '--disable-default-snat '
        '--quiet'.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testDisableDefaultSnatMissingIPAlias(self):
    command = (
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-private-nodes '
        '--main-ipv4-cidr=172.16.10.0/28 '
        '--disable-default-snat '
        '--quiet '.format(name=self.CLUSTER_NAME))
    self.AssertRaisesExceptionMatches(
        c_util.Error,
        api_adapter.DISABLE_DEFAULT_SNAT_WITHOUT_IP_ALIAS_ERROR_MSG, self.Run,
        command)

  def testDisableDefaultSnatMissingPrivateNodes(self):
    command = (
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-ip-alias '
        '--main-ipv4-cidr=172.16.10.0/28 '
        '--disable-default-snat '
        '--quiet '.format(name=self.CLUSTER_NAME))
    self.AssertRaisesExceptionMatches(
        c_util.Error,
        api_adapter.DISABLE_DEFAULT_SNAT_WITHOUT_PRIVATE_NODES_ERROR_MSG,
        self.Run, command)

  def testEnableL4ILBSubsetting(self):
    cluster_kwargs = {}
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    expected_cluster.networkConfig = (
        self.messages.NetworkConfig(enableL4ilbSubsetting=True))
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-l4-ilb-subsetting '
        '--quiet '.format(name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testShieldedInstanceConfig(self):
    cluster_kwargs = {
        'shieldedInstanceConfig':
            self.messages.ShieldedInstanceConfig(
                enableSecureBoot=True, enableIntegrityMonitoring=False),
    }
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    self.Run('{clusters_command_base} create {name} '
             '--shielded-secure-boot '
             '--no-shielded-integrity-monitoring '
             '--quiet'.format(
                 clusters_command_base=self.clusters_command_base.format(
                     self.ZONE),
                 name=self.CLUSTER_NAME))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  def testSystemConfigFromFile(self):
    cluster_kwargs = {
        'linuxNodeConfig':
            self.msgs.LinuxNodeConfig(
                sysctls=self.msgs.LinuxNodeConfig
                .SysctlsValue(additionalProperties=[
                    self.msgs.LinuxNodeConfig.SysctlsValue.AdditionalProperty(
                        key='net.core.somaxconn', value='2048'),
                    self.msgs.LinuxNodeConfig.SysctlsValue.AdditionalProperty(
                        key='net.ipv4.tcp_rmem', value='4096 87380 6291456'),
                ])),
        'kubeletConfig':
            self.msgs.NodeKubeletConfig(
                cpuManagerPolicy='static',
                cpuCfsQuota=True,
                cpuCfsQuotaPeriod='10ms'),
    }
    expected_cluster = self._MakeCluster(**cluster_kwargs)
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)
    system_config_file = self.Touch(
        self.temp_path,
        contents="""
kubeletConfig:
  cpuManagerPolicy: static
  cpuCFSQuota: true
  cpuCFSQuotaPeriod: 10ms
linuxConfig:
  sysctl:
    net.ipv4.tcp_rmem: '4096 87380 6291456'
    net.core.somaxconn: '2048'
        """)
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--system-config-from-file {system_config_file} '
        '--quiet'.format(
            name=self.CLUSTER_NAME, system_config_file=system_config_file))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')

  @parameterized.parameters(
      ("""
unknown: value
""", 'Invalid node config: unknown fields: [\'unknown\'] in "<root>"'),
      ("""
kubeletConfig:
  unknown: value
""", 'Invalid node config: unknown fields: [\'unknown\'] in "kubeletConfig"'),
      ("""
kubeletConfig:
  cpuCFSQuota: 'false'
""", 'Invalid node config: value of "cpuCFSQuota" must be bool'),
      ("""
linuxConfig:
  sysctl:
    net.core.somaxconn: 1024
""", 'Invalid node config: value of "net.core.somaxconn" must be str'),
  )
  def testSystemConfigFromFileBadConfig(self, system_config_content,
                                        expected_msg):
    with self.AssertRaisesExceptionMatches(c_util.Error, expected_msg):
      system_config_file = self.Touch(
          self.temp_path, contents=system_config_content)
      self.Run('{base} create {name} --quiet '
               '--system-config-from-file {system_config_file}'.format(
                   base=self.clusters_command_base.format(self.ZONE),
                   name=self.CLUSTER_NAME,
                   system_config_file=system_config_file))

  @parameterized.parameters(
      ('--enable-cost-management', True),
      ('--no-enable-cost-management', False),
      ('', False),
  )
  def testCostManagementConfig(self, flags, enabled):
    expected_cluster, return_cluster = self.makeExpectedAndReturnClusters({})
    if enabled:
      expected_cluster.costManagementConfig = \
          self.messages.CostManagementConfig(enabled=True)
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetCluster(return_cluster)
    self.Run('{base} create {name} {flags} --quiet'.format(
        base=self.clusters_command_base.format(self.ZONE),
        name=self.CLUSTER_NAME,
        flags=flags))

  @parameterized.parameters(
      (' --enable-main-global-access ', True),
      (' --no-enable-main-global-access ', False),
  )
  def testEnableMainGlobalAccess(self, flags, enabled):
    cluster_kwargs = {
        'name': self.CLUSTER_NAME,
    }

    expected_cluster = self._MakeCluster(**cluster_kwargs)
    policy = self._MakeIPAllocationPolicy(
        createSubnetwork=False,
        useIpAliases=True,
    )
    expected_cluster.ipAllocationPolicy = policy
    main_global_access_config = self.msgs.PrivateClusterMainGlobalAccessConfig(
        enabled=enabled)
    config = self._MakePrivateClusterConfig(
        mainGlobalAccessConfig=main_global_access_config,
        enablePrivateNodes=True,
        mainIpv4Cidr='172.16.10.0/28')
    expected_cluster.privateClusterConfig = config
    self.ExpectCreateCluster(expected_cluster, self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    return_args = cluster_kwargs.copy()
    self.updateResponse(return_args)
    return_cluster = self._MakeCluster(**return_args)
    self.ExpectGetCluster(return_cluster)

    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' create {name} '
        '--enable-ip-alias '
        '--private-cluster '
        '--main-ipv4-cidr=172.16.10.0/28 '
        '{flags}'
        '--quiet'.format(name=self.CLUSTER_NAME, flags=flags))
    self.AssertOutputContains('RUNNING')
    self.AssertErrContains('Created')


if __name__ == '__main__':
  test_case.main()
