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
"""Test of the 'node-pools create' command."""
from __future__ import absolute_import
from __future__ import unicode_literals
import json

from googlecloudsdk.api_lib.container import util as c_util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.container import base


class CreateTestGA(parameterized.TestCase, base.TestBaseV1, base.GATestBase,
                   base.NodePoolsTestBase):
  """gcloud GA track using container v1 API."""

  def updateResponse(self, node_pool, **kwargs):
    """Update the CreateNodePool response with fake values."""
    fake = {
        'nodeVersion': self.VERSION,
    }
    node_pool.update(fake)
    node_pool.update(kwargs)

  # TODO(b/64575339) Make all these tests use this.
  def makeExpectedAndReturnNodePools(self, pool_kwargs):
    """Create mock nodepool objects."""
    expected_pool = self._MakeNodePool(**pool_kwargs)
    return_kwargs = pool_kwargs.copy()
    self.updateResponse(return_kwargs)
    return_pool = self._MakeNodePool(**return_kwargs)
    return expected_pool, return_pool

  def _TestCreateDefaults(self, location):
    self.assertIsNone(c_util.ClusterConfig.Load(self.CLUSTER_NAME, location,
                                                self.PROJECT_ID))
    kwargs = {'zone': location}
    self.ExpectCreateNodePool(
        self._MakeNodePool(),
        self._MakeNodePoolOperation(**kwargs),
        zone=location)
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done,
                                                        **kwargs))

    pool_kwargs = {'nodeVersion': self.VERSION}
    pool = self._MakeNodePool(**pool_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool, zone=location)

    if location == self.REGION:
      self.Run(self.regional_node_pools_command_base.format(location) +
               ' create {0} --cluster={1}'.format(self.NODE_POOL_NAME,
                                                  self.CLUSTER_NAME))
    else:
      self.Run(self.node_pools_command_base.format(location) +
               ' create {0} --cluster={1}'.format(self.NODE_POOL_NAME,
                                                  self.CLUSTER_NAME))
    self.AssertErrContains('Created')
    self.AssertOutputMatches(
        (r'NAME MACHINE_TYPE DISK_SIZE_GB NODE_VERSION\n'
         '{name} {version}\\n')
        .format(name=pool.name,
                version=pool.version),
        normalize_space=True)

  def testCreateDefaults(self):
    self._TestCreateDefaults(self.ZONE)

  def testCreateDefaultsRegional(self):
    self._TestCreateDefaults(self.REGION)

  def testCreateDefaultsJsonOutput(self):
    self.assertIsNone(c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                                self.PROJECT_ID))
    self.ExpectCreateNodePool(self._MakeNodePool(),
                              self._MakeNodePoolOperation())
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    pool = self._MakeNodePool(nodeVersion=self.VERSION)
    self.ExpectGetNodePool(pool.name, response=pool)

    self.Run(self.node_pools_command_base.format(self.ZONE) +
             ' create {0} --cluster={1} --format json'.format(
                 self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.AssertErrContains('Created')
    json_pool = json.loads(self.GetOutput())
    self.assertEqual(len(json_pool), 1)
    self.assertEqual(json_pool[0]['name'], str(self.NODE_POOL_NAME))
    self.assertEqual(json_pool[0]['version'], str(self.VERSION))

  def testCreateNoDefaults(self):
    properties.VALUES.container.new_scopes_behavior.Set(True)
    self.assertIsNone(c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                                self.PROJECT_ID))
    pool_kwargs = {
        'name':
            'my-custom-pool',
        'clusterId':
            self.CLUSTER_NAME,
        'initialNodeCount':
            5,
        'machineType':
            'n1-standard-7',  # Yup, a 7 core machine.
        'diskSizeGb':
            61,
        'diskType':
            'pd-ssd',
        'nodeVersion':
            '1.7.5',
        'localSsdCount':
            2,
        'tags': ['http-server', 'https-server'],
        'nodeLabels':
            self.msgs.NodeConfig.LabelsValue(
                additionalProperties=[
                    self.msgs.NodeConfig.LabelsValue.AdditionalProperty(
                        key='env', value='prod'),
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
        'oauthScopes': [
            'https://www.googleapis.com/auth/devstorage.read_only',
            'https://www.googleapis.com/auth/logging.write',
            'https://www.googleapis.com/auth/monitoring',
            'https://www.googleapis.com/auth/service.management.readonly',
            'https://www.googleapis.com/auth/servicecontrol',
            'https://www.googleapis.com/auth/trace.append',
        ],
    }

    self.ExpectCreateNodePool(
        self._MakeNodePool(**pool_kwargs),
        self._MakeNodePoolOperation(
            targetLink=self.NODE_POOL_TARGET_LINK.format(
                self.API_VERSION, self.PROJECT_NUM, self.ZONE,
                self.CLUSTER_NAME, pool_kwargs['name'])))
    self.ExpectGetOperation(self._MakeNodePoolOperation(
        targetLink=self.NODE_POOL_TARGET_LINK.format(
            self.API_VERSION,
            self.PROJECT_NUM,
            self.ZONE,
            self.CLUSTER_NAME,
            pool_kwargs['name']),
        status=self.op_done))

    pool_version_kwargs = pool_kwargs.copy()
    pool = self._MakeNodePool(**pool_version_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool)

    self.Run(
        self.node_pools_command_base.format(self.ZONE) + ' create {name}'
        ' --cluster={clusterId}'
        ' --node-version={nodeVersion}'
        ' --num-nodes=5'
        ' --machine-type={machineType}'
        ' --disk-size={diskSizeGb}'
        ' --disk-type={diskType}'
        ' --local-ssd-count={localSsdCount}'
        ' --tags=http-server,https-server'
        ' --node-labels=env=prod'
        ' --node-taints=key1=val1:NoSchedule'
        ' --enable-autoscaling'
        ' --min-nodes=1'
        ' --max-nodes=5'
        ' --image-type={imageType}'
        ' --image=cos-63'
        ' --image-family=cos-cloud'
        ' --image-project=gke-node-images'
        ' --preemptible'
        ' --enable-autoupgrade'
        ' --enable-autorepair'.format(**pool_kwargs))
    self.AssertErrContains("""This will enable the autorepair feature for \
nodes. Please see
https://cloud.google.com/kubernetes-engine/docs/node-auto-repair for more
information on node autorepairs.

This will enable the autoupgrade feature for nodes. Please see
https://cloud.google.com/kubernetes-engine/docs/node-management for more
information on node autoupgrades.

<START PROGRESS TRACKER>Creating node pool my-custom-pool
<END PROGRESS TRACKER>SUCCESS
Created [https://container.googleapis.com/{0}/projects/fake-project-id/zones/us-central1-f/clusters/my-cluster/nodePools/my-custom-pool].
""".format(self.API_VERSION))
    self.AssertOutputMatches(
        (r'NAME MACHINE_TYPE DISK_SIZE_GB NODE_VERSION\n'
         '{name} {machine_type} {disk_size} {version}\\n')
        .format(name=pool.name,
                machine_type=pool.config.machineType,
                disk_size=pool.config.diskSizeGb,
                version=pool.version),
        normalize_space=True)

  @parameterized.parameters(('--service-account=my-sa --scopes=gke-default',
                             cli_test_base.MockArgumentError, 'At most one of'))
  def testNodeIdentityMutex(self, flags, expected_err, expected_msg):
    with self.AssertRaisesExceptionMatches(expected_err, expected_msg):
      self.Run('{base} create {name} --cluster {cluster_name} --quiet {flags}'.
               format(
                   base=self.node_pools_command_base.format(self.ZONE),
                   name=self.NODE_POOL_NAME,
                   cluster_name=self.CLUSTER_NAME,
                   flags=flags))

  def testServiceAccountCloudPlatformScope(self):
    pool_kwargs = {
        'serviceAccount': 'my-sa',
        'oauthScopes': ['https://www.googleapis.com/auth/cloud-platform',
                        'https://www.googleapis.com/auth/userinfo.email'],
    }
    expected_pool, return_pool = self.makeExpectedAndReturnNodePools(
        pool_kwargs)
    # Create node pool expects node pool and returns pending operation.
    self.ExpectCreateNodePool(expected_pool, self._MakeNodePoolOperation())
    # Get operation returns done operation.
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    # Get returns expected cluster, populated with other fields by server.
    self.ExpectGetNodePool(return_pool.name, response=return_pool)
    self.Run('{base} create {name} '
             '--service-account=my-sa '
             '--cluster {clusterName}'.format(
                 base=self.node_pools_command_base.format(self.ZONE),
                 name=self.NODE_POOL_NAME,
                 clusterName=self.CLUSTER_NAME))

  def _testScopes(self, flags, scopes):
    pool_kwargs = {
        # Sort the scopes to assert equality of the lists
        'oauthScopes': sorted(scopes),
    }
    expected_pool, return_pool = self.makeExpectedAndReturnNodePools(
        pool_kwargs)
    # Create node pool expects node pool and returns pending operation.
    self.ExpectCreateNodePool(expected_pool, self._MakeNodePoolOperation())
    # Get operation returns done operation.
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    # Get returns expected cluster, populated with other fields by server.
    self.ExpectGetNodePool(return_pool.name, response=return_pool)
    self.Run('{base} create {name} {flags} '
             '--cluster {clusterName}'.format(
                 base=self.node_pools_command_base.format(self.ZONE),
                 name=self.NODE_POOL_NAME,
                 flags=flags,
                 clusterName=self.CLUSTER_NAME))

  def testCreateWithNodeTaints(self):
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                  self.PROJECT_ID))
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
    pool_kwargs = {
        'name': 'my-custom-pool',
        'clusterId': self.CLUSTER_NAME,
        'nodeTaints': taints
    }
    self.ExpectCreateNodePool(
        self._MakeNodePool(**pool_kwargs),
        self._MakeNodePoolOperation(**pool_kwargs))
    self.ExpectGetOperation(
        self._MakeNodePoolOperation(status=self.op_done, **pool_kwargs))

    pool_version_kwargs = pool_kwargs.copy()
    pool_version_kwargs.update({'nodeVersion': self.VERSION})
    pool = self._MakeNodePool(**pool_version_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool)
    self.Run(
        self.node_pools_command_base.format(self.ZONE) + ' create {name}'
        ' --cluster={clusterId}'
        ' --node-taints='
        'key1=val1:NoSchedule,key2=val2:PreferNoSchedule,key3=val3:NoExecute'
        .format(**pool_kwargs))
    self.AssertOutputEquals(
        ('NAME MACHINE_TYPE DISK_SIZE_GB NODE_VERSION\n'
         '{name} {version}\n').format(name=pool.name, version=pool.version),
        normalize_space=True)

  def testCreateMissingCluster(self):
    with self.assertRaises(properties.RequiredPropertyError):
      self.Run(self.node_pools_command_base.format(self.ZONE) +
               ' create {0}'.format(self.NODE_POOL_NAME))
    self.AssertErrContains(
        'The required property [cluster] is not currently set.')

  def testCreateMissingZone(self):
    with self.assertRaises(exceptions.MinimumArgumentException):
      self.Run(self.COMMAND_BASE + ' node-pools create {0} --cluster={1}'
               .format(self.NODE_POOL_NAME, self.CLUSTER_NAME))

  def testCreateMissingProject(self):
    properties.VALUES.core.project.Set(None)
    with self.assertRaises(properties.RequiredPropertyError):
      self.Run(self.node_pools_command_base.format(self.ZONE) +
               ' create {0} --cluster={1}'.format(self.NODE_POOL_NAME,
                                                  self.CLUSTER_NAME))
    self.AssertErrContains(
        'The required property [project] is not currently set.')

  def testCreateHttpError(self):
    self.assertIsNone(c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                                self.PROJECT_ID))
    self.ExpectCreateNodePool(self._MakeNodePool(), exception=self.HttpError())

    with self.assertRaises(exceptions.HttpException):
      self.Run(self.node_pools_command_base.format(self.ZONE) +
               ' create {0} --cluster={1}'.format(self.NODE_POOL_NAME,
                                                  self.CLUSTER_NAME))
    self.AssertErrContains(
        'ResponseError: code=400, message=your request is bad '
        'and you should feel bad.')

  def testCreateInvalidNodeLabels(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(self.node_pools_command_base.format(self.ZONE) +
               ' create {0} --cluster={1} --node-labels=test=a,b'
               .format(self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.AssertErrContains('argument --node-labels')

  def testCreateEmptyTags(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(self.node_pools_command_base.format(self.ZONE) +
               ' create {0} --cluster={1} --tags='
               .format(self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.AssertErrContains('argument --tags')

  def testCreateInvalidNodeTaints(self):
    with self.assertRaises(c_util.Error):
      self.Run(self.node_pools_command_base.format(self.ZONE) +
               ' create {0} --cluster={1} --node-taints=test=ab'
               .format(self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.AssertErrContains('argument --node-taints')

  def testCreateInvalidNodeTaintEffect(self):
    with self.assertRaises(c_util.Error):
      self.Run(self.node_pools_command_base.format(self.ZONE) +
               ' create {0} --cluster={1} --node-taints=test=ab:RandomEffect'
               .format(self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.AssertErrContains('argument --node-taints')


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
      self.Run('{base} create {name} --cluster {cluster_name} --quiet {flags}'.
               format(
                   base=self.node_pools_command_base.format(self.ZONE),
                   name=self.NODE_POOL_NAME,
                   cluster_name=self.CLUSTER_NAME,
                   flags=flags))

  @parameterized.parameters(('--enable-cloud-endpoints', c_util.Error,
                             '--[no-]enable-cloud-endpoints is not allowed'),
                            ('--no-enable-cloud-endpoints', c_util.Error,
                             '--[no-]enable-cloud-endpoints is not allowed'))
  def testNoEnableCloudEndpointsNewScopesBehaviorMutex(
      self, flags, expected_err, expected_msg):
    properties.VALUES.container.new_scopes_behavior.Set(True)
    with self.AssertRaisesExceptionMatches(expected_err, expected_msg):
      self.Run('{base} create {name} --cluster {cluster_name} --quiet {flags}'.
               format(
                   base=self.node_pools_command_base.format(self.ZONE),
                   name=self.NODE_POOL_NAME,
                   cluster_name=self.CLUSTER_NAME,
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
  def testScopesNoWarning(self, flags, scopes):
    self._testScopes(flags, scopes)
    self.AssertErrNotContains('new clusters will no longer get compute-rw')
    self.AssertErrNotContains('The behavior of --scopes will change')


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class CreateTestBetaV1API(base.BetaTestBase, CreateTestGA):
  """gcloud Beta track using container v1 API."""

  def testCreateMinCpuPlatform(self):
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                  self.PROJECT_ID))
    pool_kwargs = {
        'name': 'my-custom-pool',
        'clusterId': self.CLUSTER_NAME,
        'minCpuPlatform': 'Skylake',
    }

    self.ExpectCreateNodePool(
        self._MakeNodePool(**pool_kwargs),
        self._MakeNodePoolOperation(**pool_kwargs))

    self.ExpectGetOperation(
        self._MakeNodePoolOperation(status=self.op_done, **pool_kwargs))

    pool_version_kwargs = pool_kwargs.copy()
    pool_version_kwargs.update({'nodeVersion': self.VERSION})
    pool = self._MakeNodePool(**pool_version_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool)

    self.Run(
        self.node_pools_command_base.format(self.ZONE) + ' create {name}'
        ' --cluster={clusterId}'
        ' --min-cpu-platform=Skylake'.format(**pool_kwargs))
    self.AssertOutputEquals(
        ('NAME MACHINE_TYPE DISK_SIZE_GB NODE_VERSION\n'
         '{name} {version}\n').format(name=pool.name, version=pool.version),
        normalize_space=True)

  @parameterized.parameters(
      '--enable-cloud-endpoints',
      '--no-enable-cloud-endpoints',
  )
  def testEnableCloudEndpointsRemoved(self, flags):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'Flag --[no-]enable-cloud-endpoints has been removed'):
      self.Run('{base} create {name} --cluster {cluster_name} --quiet {flags}'.
               format(
                   base=self.node_pools_command_base.format(self.ZONE),
                   name=self.NODE_POOL_NAME,
                   cluster_name=self.CLUSTER_NAME,
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

  def testCreateBetaFeatures(self):
    m = self.messages
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                  self.PROJECT_ID))
    pool_kwargs = {
        'name':
            'my-custom-pool',
        'clusterId':
            self.CLUSTER_NAME,
        'workloadMetadataConfig':
            m.WorkloadMetadataConfig(nodeMetadata=m.WorkloadMetadataConfig.
                                     NodeMetadataValueValuesEnum.SECURE),
    }

    self.ExpectCreateNodePool(
        self._MakeNodePool(**pool_kwargs),
        self._MakeNodePoolOperation(**pool_kwargs))

    self.ExpectGetOperation(
        self._MakeNodePoolOperation(status=self.op_done, **pool_kwargs))

    pool_version_kwargs = pool_kwargs.copy()
    pool_version_kwargs.update({'nodeVersion': self.VERSION})
    pool = self._MakeNodePool(**pool_version_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool)

    self.Run(
        self.node_pools_command_base.format(self.ZONE) + ' create {name}'
        ' --cluster={clusterId}'
        ' --workload-metadata-from-node=secure'.format(**pool_kwargs))
    self.AssertOutputEquals(
        ('NAME MACHINE_TYPE DISK_SIZE_GB NODE_VERSION\n'
         '{name} {version}\n').format(name=pool.name, version=pool.version),
        normalize_space=True)


# Mixin class must come in first to have the correct multi-inheritance behavior.
class CreateTestAlphaV1API(base.AlphaTestBase, CreateTestBetaV1API):
  """gcloud Alpha track using container v1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(True)

  def testCreateInvalidacceleratorMissingType(self):
    properties.VALUES.core.disable_prompts.Set(False)
    with self.AssertRaisesArgumentErrorMatches(
        r'argument --accelerator: Key [type] required in dict arg but not '
        r'provided'):
      self.Run(
          self.node_pools_command_base.format(self.ZONE) +
          ' create {0} --accelerator=count=2'.format(self.CLUSTER_NAME))

  def testCreateWithValidAccelerators(self):
    m = self.messages
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                  self.PROJECT_ID))
    pool_kwargs = {
        'name':
            'my-custom-pool',
        'clusterId':
            self.CLUSTER_NAME,
        'accelerators': [
            m.AcceleratorConfig(acceleratorType='nvidia-tesla-k80',
                                acceleratorCount=int(2))
        ],
    }

    self.ExpectCreateNodePool(
        self._MakeNodePool(**pool_kwargs),
        self._MakeNodePoolOperation(**pool_kwargs))

    self.ExpectGetOperation(
        self._MakeNodePoolOperation(status=self.op_done, **pool_kwargs))

    pool_version_kwargs = pool_kwargs.copy()
    pool_version_kwargs.update({'nodeVersion': self.VERSION})
    pool = self._MakeNodePool(**pool_version_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool)

    self.Run(
        self.node_pools_command_base.format(self.ZONE) + ' create {name}'
        ' --cluster={clusterId}'
        ' --accelerator=type=nvidia-tesla-k80,count=2'.format(**pool_kwargs))
    self.AssertOutputMatches(
        (r'NAME MACHINE_TYPE DISK_SIZE_GB NODE_VERSION\n'
         '{name} {version}\\n').format(name=pool.name, version=pool.version),
        normalize_space=True)

  def testAcceleratorCountDefaulting(self):
    m = self.messages
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                  self.PROJECT_ID))
    pool_kwargs = {
        'name':
            'my-custom-pool',
        'clusterId':
            self.CLUSTER_NAME,
        'accelerators': [
            m.AcceleratorConfig(acceleratorType='nvidia-tesla-k80',
                                acceleratorCount=int(1))
        ],
    }

    self.ExpectCreateNodePool(
        self._MakeNodePool(**pool_kwargs),
        self._MakeNodePoolOperation(**pool_kwargs))

    self.ExpectGetOperation(
        self._MakeNodePoolOperation(status=self.op_done, **pool_kwargs))

    pool_version_kwargs = pool_kwargs.copy()
    pool_version_kwargs.update({'nodeVersion': self.VERSION})
    pool = self._MakeNodePool(**pool_version_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool)

    self.Run(
        self.node_pools_command_base.format(self.ZONE) + ' create {name}'
        ' --cluster={clusterId}'
        ' --accelerator=type=nvidia-tesla-k80'.format(**pool_kwargs))
    self.AssertOutputMatches(
        (r'NAME MACHINE_TYPE DISK_SIZE_GB NODE_VERSION\n'
         '{name} {version}\\n').format(name=pool.name, version=pool.version),
        normalize_space=True)


# Mixin class must come in first to have the correct multi-inheritance behavior.
class CreateTestAlphaV1Alpha1API(base.TestBaseV1Alpha1, CreateTestAlphaV1API):
  """gcloud Alpha track using container v1alpha1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(False)

  def testCreateAlphaFeatures(self):
    m = self.messages
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                  self.PROJECT_ID))
    format_enum = self.messages.LocalSsdVolumeConfig.FormatValueValuesEnum
    pool_kwargs = {
        'name':
            'my-custom-pool',
        'clusterId':
            self.CLUSTER_NAME,
        'workloadMetadataConfig':
            m.WorkloadMetadataConfig(nodeMetadata=m.WorkloadMetadataConfig.
                                     NodeMetadataValueValuesEnum.SECURE),
        'localSsdVolumeConfigs': [
            m.LocalSsdVolumeConfig(count=2, type='nvme',
                                   format=format_enum.FS),
            m.LocalSsdVolumeConfig(count=1, type='scsi',
                                   format=format_enum.BLOCK),
        ],
        'autoscaling':
            m.NodePoolAutoscaling(
                enabled=True, maxNodeCount=6, autoprovisioned=True),
    }

    self.ExpectCreateNodePool(
        self._MakeNodePool(**pool_kwargs),
        self._MakeNodePoolOperation(**pool_kwargs))

    self.ExpectGetOperation(
        self._MakeNodePoolOperation(status=self.op_done, **pool_kwargs))

    pool_version_kwargs = pool_kwargs.copy()
    pool_version_kwargs.update({'nodeVersion': self.VERSION})
    pool = self._MakeNodePool(**pool_version_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool)

    self.Run(
        self.node_pools_command_base.format(self.ZONE) + ' create {name}'
        ' --cluster={clusterId}'
        ' --local-ssd-volumes count=2,type=nvme,format=fs'
        ' --local-ssd-volumes count=1,type=scsi,format=block'
        ' --enable-autoscaling --enable-autoprovisioning --max-nodes 6'
        ' --workload-metadata-from-node=secure'.format(**pool_kwargs))
    self.AssertOutputEquals(
        ('NAME MACHINE_TYPE DISK_SIZE_GB NODE_VERSION\n'
         '{name} {version}\n').format(name=pool.name, version=pool.version),
        normalize_space=True)

  @parameterized.parameters(
      (1, 'notatype', 'fs'),
      (4, 'scsi', 'notaformat'),
      ('notacount', 'scsi', 'fs'),
      (0, 'scsi', 'fs'))
  def testCreateInvalidLocalSsdVolumeConfig(self, ssd_count, ssd_type,
                                            ssd_format):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.node_pools_command_base.format(self.ZONE) +
          ' create {0} --cluster={1} --local-ssd-volumes '
          'count={2},type={3},format={4}'.format(self.NODE_POOL_NAME,
                                                 self.CLUSTER_NAME, ssd_count,
                                                 ssd_type, ssd_format))
    self.AssertErrContains('argument --local-ssd-volumes')

  def testCreateEmptyLocalSsdVolumeConfig(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.node_pools_command_base.format(self.ZONE) +
          ' create {0} --cluster={1} --local-ssd-volumes'.format(
              self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.AssertErrContains('argument --local-ssd-volumes')


if __name__ == '__main__':
  test_case.main()
