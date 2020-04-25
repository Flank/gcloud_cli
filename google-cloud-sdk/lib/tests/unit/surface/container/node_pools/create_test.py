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
"""Test of the 'node-pools create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib.container import util as c_util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.container import base


class CreateTestGA(parameterized.TestCase, base.GATestBase,
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
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, location, self.PROJECT_ID))
    kwargs = {'zone': location}
    pool_kwargs = {}
    self.ExpectCreateNodePool(
        self._MakeNodePool(**pool_kwargs),
        self._MakeNodePoolOperation(**kwargs),
        zone=location)
    self.ExpectGetOperation(
        self._MakeNodePoolOperation(status=self.op_done, **kwargs))

    pool_kwargs = {'nodeVersion': self.VERSION}
    pool = self._MakeNodePool(**pool_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool, zone=location)

    if location == self.REGION:
      self.Run(
          self.regional_node_pools_command_base.format(location) +
          ' create {0} --cluster={1}'.format(self.NODE_POOL_NAME,
                                             self.CLUSTER_NAME))
    else:
      self.Run(
          self.node_pools_command_base.format(location) +
          ' create {0} --cluster={1}'.format(self.NODE_POOL_NAME,
                                             self.CLUSTER_NAME))
    self.AssertErrContains('Created')
    self.AssertOutputMatches(
        (r'NAME MACHINE_TYPE DISK_SIZE_GB NODE_VERSION\n'
         '{name} {version}\\n').format(name=pool.name, version=pool.version),
        normalize_space=True)

  def testCreateDefaults(self):
    self._TestCreateDefaults(self.ZONE)

  def testCreateDefaultsRegional(self):
    self._TestCreateDefaults(self.REGION)

  def testCreateDefaultsJsonOutput(self):
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                  self.PROJECT_ID))
    pool_kwargs = {}
    self.ExpectCreateNodePool(
        self._MakeNodePool(**pool_kwargs), self._MakeNodePoolOperation())
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    pool = self._MakeNodePool(nodeVersion=self.VERSION)
    self.ExpectGetNodePool(pool.name, response=pool)

    self.Run(
        self.node_pools_command_base.format(self.ZONE) +
        ' create {0} --cluster={1} --format json'.format(
            self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.AssertErrContains('Created')
    json_pool = json.loads(self.GetOutput())
    self.assertEqual(len(json_pool), 1)
    self.assertEqual(json_pool[0]['name'], str(self.NODE_POOL_NAME))
    self.assertEqual(json_pool[0]['version'], str(self.VERSION))

  def testCreateNoDefaults(self):
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
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
                enabled=True,
                minNodeCount=1,
                maxNodeCount=5,
                autoprovisioned=True),
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
        'metadata':
            self.msgs.NodeConfig.MetadataValue(additionalProperties=[
                self.msgs.NodeConfig.MetadataValue.AdditionalProperty(
                    key=key, value=value)
                for key, value in [('key', 'value'), ('key2', 'value2')]
            ]),
        'maxPodsConstraint':
            self.msgs.MaxPodsConstraint(maxPodsPerNode=30),
        'sandboxConfig':
            self.msgs.SandboxConfig(
                type=self.msgs.SandboxConfig.TypeValueValuesEnum.GVISOR),
    }

    self.ExpectCreateNodePool(
        self._MakeNodePool(**pool_kwargs),
        self._MakeNodePoolOperation(
            targetLink=self.NODE_POOL_TARGET_LINK.format(
                self.API_VERSION, self.PROJECT_NUM, self.ZONE,
                self.CLUSTER_NAME, pool_kwargs['name'])))
    self.ExpectGetOperation(
        self._MakeNodePoolOperation(
            targetLink=self.NODE_POOL_TARGET_LINK.format(
                self.API_VERSION, self.PROJECT_NUM, self.ZONE,
                self.CLUSTER_NAME, pool_kwargs['name']),
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
        ' --enable-autoprovisioning'
        ' --enable-autoscaling'
        ' --min-nodes=1'
        ' --max-nodes=5'
        ' --image-type={imageType}'
        ' --image=cos-63'
        ' --image-family=cos-cloud'
        ' --image-project=gke-node-images'
        ' --preemptible'
        ' --enable-autoupgrade'
        ' --enable-autorepair'
        ' --metadata key=value,key2=value2'
        ' --max-pods-per-node=30'
        ' --sandbox type=gvisor'.format(**pool_kwargs))
    # pylint: disable=line-too-long
    self.AssertErrContains(
        """WARNING: Starting in 1.12, new node pools will be created with \
their legacy Compute Engine instance metadata APIs disabled by default. To \
create a node pool with legacy instance metadata endpoints disabled, run \
`node-pools create` with the flag `--metadata disable-legacy-endpoints=true`.
This will enable the autorepair feature for \
nodes. Please see \
https://cloud.google.com/kubernetes-engine/docs/node-auto-repair for more \
information on node autorepairs.
{{"ux": "PROGRESS_TRACKER", "message": "Creating node pool my-custom-pool", \
"status": "SUCCESS"}}
Created \
[https://container.googleapis.com/{0}/projects/fake-project-id/zones/us-central1-f/clusters/my-cluster/nodePools/my-custom-pool].
""".format(self.API_VERSION))
    # pylint: enable=line-too-long
    self.AssertOutputMatches(
        (r'NAME MACHINE_TYPE DISK_SIZE_GB NODE_VERSION\n'
         '{name} {machine_type} {disk_size} {version}\\n').format(
             name=pool.name,
             machine_type=pool.config.machineType,
             disk_size=pool.config.diskSizeGb,
             version=pool.version),
        normalize_space=True)

  @parameterized.parameters(
      ('', '', True),
      ('--image-type', 'COS', True),
      ('--image-type', 'UBUNTU', False),
  )
  def testAutoRepairDefaults(self, image_flag, image_value, expect_autorepair):
    pool_kwargs = {
        'management': self._MakeDefaultNodeManagement(expect_autorepair),
        'imageType': image_value if image_value else None,
    }
    expected_pool, return_pool = self.makeExpectedAndReturnNodePools(
        pool_kwargs)
    self.ExpectCreateNodePool(expected_pool, self._MakeNodePoolOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetNodePool(return_pool.name, response=return_pool)
    self.Run('{base} create {name} {flag} {value} '
             '--quiet --cluster {clusterName}'.format(
                 base=self.node_pools_command_base.format(self.ZONE),
                 name=self.NODE_POOL_NAME,
                 flag=image_flag,
                 value=image_value,
                 clusterName=self.CLUSTER_NAME))

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

  def testServiceAccountCloudPlatformScope(self):
    pool_kwargs = {
        'serviceAccount':
            'my-sa',
        'oauthScopes': [
            'https://www.googleapis.com/auth/cloud-platform',
            'https://www.googleapis.com/auth/userinfo.email'
        ],
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

  def testServiceAccountCustomScopes(self):
    pool_kwargs = {
        'serviceAccount': 'my-sa',
        'oauthScopes': ['something-else',],
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
             '--scopes=something-else '
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
            key='key1', value='val1', effect=effect_enum.NO_SCHEDULE),
        self.msgs.NodeTaint(
            key='key2', value='val2', effect=effect_enum.PREFER_NO_SCHEDULE),
        self.msgs.NodeTaint(
            key='key3', value='val3', effect=effect_enum.NO_EXECUTE)
    ]
    pool_kwargs = {
        'name': 'my-custom-pool',
        'clusterId': self.CLUSTER_NAME,
        'nodeTaints': taints,
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
      self.Run(
          self.node_pools_command_base.format(self.ZONE) +
          ' create {0}'.format(self.NODE_POOL_NAME))
    self.AssertErrContains(
        'The required property [cluster] is not currently set.')

  def testCreateMissingZone(self):
    with self.assertRaises(exceptions.MinimumArgumentException):
      self.Run(self.COMMAND_BASE +
               ' node-pools create {0} --cluster={1}'.format(
                   self.NODE_POOL_NAME, self.CLUSTER_NAME))

  def testCreateMissingProject(self):
    properties.VALUES.core.project.Set(None)
    with self.assertRaises(properties.RequiredPropertyError):
      self.Run(
          self.node_pools_command_base.format(self.ZONE) +
          ' create {0} --cluster={1}'.format(self.NODE_POOL_NAME,
                                             self.CLUSTER_NAME))
    self.AssertErrContains(
        'The required property [project] is not currently set.')

  def testCreateHttpError(self):
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                  self.PROJECT_ID))
    pool_kwargs = {}
    self.ExpectCreateNodePool(
        self._MakeNodePool(**pool_kwargs), exception=self.HttpError())

    with self.assertRaises(exceptions.HttpException):
      self.Run(
          self.node_pools_command_base.format(self.ZONE) +
          ' create {0} --cluster={1}'.format(self.NODE_POOL_NAME,
                                             self.CLUSTER_NAME))
    self.AssertErrContains(
        'ResponseError: code=400, message=your request is bad '
        'and you should feel bad.')

  def testCreateInvalidNodeLabels(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.node_pools_command_base.format(self.ZONE) +
          ' create {0} --cluster={1} --node-labels=test=a,b'.format(
              self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.AssertErrContains('argument --node-labels')

  def testCreateEmptyTags(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.node_pools_command_base.format(self.ZONE) +
          ' create {0} --cluster={1} --tags='.format(self.NODE_POOL_NAME,
                                                     self.CLUSTER_NAME))
    self.AssertErrContains('argument --tags')

  def testCreateInvalidNodeTaints(self):
    with self.assertRaises(c_util.Error):
      self.Run(
          self.node_pools_command_base.format(self.ZONE) +
          ' create {0} --cluster={1} --node-taints=test=ab'.format(
              self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.AssertErrContains('argument --node-taints')

  def testCreateInvalidNodeTaintEffect(self):
    with self.assertRaises(c_util.Error):
      self.Run(
          self.node_pools_command_base.format(self.ZONE) +
          ' create {0} --cluster={1} --node-taints=test=ab:RandomEffect'.format(
              self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.AssertErrContains('argument --node-taints')

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
            m.AcceleratorConfig(
                acceleratorType='nvidia-tesla-k80', acceleratorCount=int(2))
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
            m.AcceleratorConfig(
                acceleratorType='nvidia-tesla-k80', acceleratorCount=int(1))
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

  def testNodeModificationWarning(self):
    pool_kwargs = {
        'imageType': 'ubuntu',
    }
    expected_pool, return_pool = self.makeExpectedAndReturnNodePools(
        pool_kwargs)
    self.ExpectCreateNodePool(expected_pool, self._MakeNodePoolOperation())
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    self.ExpectGetNodePool(return_pool.name, response=return_pool)
    self.Run('{base} create {name} --cluster {clusterName} --image-type=ubuntu '
             '--enable-autorepair'.format(
                 base=self.node_pools_command_base.format(self.ZONE),
                 name=self.NODE_POOL_NAME,
                 clusterName=self.CLUSTER_NAME))
    self.AssertErrContains('Created')
    self.AssertErrContains(
        'Modifications on the boot disks of node VMs do not persist across '
        'node recreations. Nodes are recreated during manual-upgrade, '
        'auto-upgrade, auto-repair, and auto-scaling. To preserve '
        'modifications across node recreation, use a DaemonSet.')

  def testAutoUpgradeDefault(self):
    pool_kwargs = {
        'management':
            self.messages.NodeManagement(autoRepair=True, autoUpgrade=True)
    }
    expected_pool, return_pool = self.makeExpectedAndReturnNodePools(
        pool_kwargs)
    self.ExpectCreateNodePool(expected_pool, self._MakeNodePoolOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetNodePool(return_pool.name, response=return_pool)
    self.Run('{base} create {name} --quiet --cluster {clusterName}'.format(
        base=self.node_pools_command_base.format(self.ZONE),
        name=self.NODE_POOL_NAME,
        clusterName=self.CLUSTER_NAME))

  @parameterized.parameters(('any', ''), ('none', ''),
                            ('specific', 'reservation-specific'))
  def testReservationAffinity(self, affinity, reservation_name):
    pool_kwargs = {
        'reservationAffinity':
            self._MakeReservationAffinity(affinity, reservation_name)
    }
    expected_pool, return_pool = self.makeExpectedAndReturnNodePools(
        pool_kwargs)
    self.ExpectCreateNodePool(expected_pool, self._MakeNodePoolOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetNodePool(return_pool.name, response=return_pool)

    reservation_flags = '--reservation-affinity={}'.format(affinity)
    if affinity == 'specific':
      reservation_flags += ' --reservation={}'.format(reservation_name)
    self.Run(
        self.node_pools_command_base.format(self.ZONE) +
        ' create {0} --cluster={1} {2}'.format(
            self.NODE_POOL_NAME, self.CLUSTER_NAME, reservation_flags))

  @parameterized.parameters('any', 'none')
  def testNonSpecificReservationWith(self, affinity):
    reservation_name = 'reservation_name'
    err_msg = 'Cannot specify --reservation for --reservation-affinity={}.'.format(
        affinity)
    with self.AssertRaisesExceptionMatches(core_exceptions.Error, err_msg):
      self.Run((
          self.node_pools_command_base.format(self.ZONE) +
          ' create {0} --cluster={1} --reservation-affinity={2} --reservation={3}'
      ).format(self.NODE_POOL_NAME, self.CLUSTER_NAME, affinity,
               reservation_name))

  def testCreateWithReservationSpecificWithoutReservationName(self):
    err_msg = 'Must specify --reservation for --reservation-affinity=specific.'
    with self.AssertRaisesExceptionMatches(core_exceptions.Error, err_msg):
      self.Run(
          (self.node_pools_command_base.format(self.ZONE) +
           ' create {0} --cluster={1} --reservation-affinity=specific').format(
               self.NODE_POOL_NAME, self.CLUSTER_NAME))

  def _testNodeLocations(self, flags, locations):
    pool_kwargs = {'nodePoolLocations': locations}
    expected_pool, return_pool = self.makeExpectedAndReturnNodePools(
        pool_kwargs)
    # Create node pool expects node pool and returns pending operation.
    self.ExpectCreateNodePool(expected_pool, self._MakeNodePoolOperation())
    # Get operation returns done operation.
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    # Get returns expected node pool, populated with other fields by server.
    self.ExpectGetNodePool(return_pool.name, response=return_pool)
    self.Run('{base} create {name} {flags} '
             '--cluster {clusterName}'.format(
                 base=self.node_pools_command_base.format(self.ZONE),
                 name=self.NODE_POOL_NAME,
                 flags=flags,
                 clusterName=self.CLUSTER_NAME))

  def testNodeLocations(self):
    self._testNodeLocations(
        '--node-locations=us-central1-a,us-central1-b',
        locations=['us-central1-a', 'us-central1-b'])

  def _testWorkloadMetadata(self, flags, config):
    expected_pool, return_pool = self.makeExpectedAndReturnNodePools({})
    expected_pool.config.workloadMetadataConfig = config
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

  def testWorkloadMetadataDefault(self):
    self._testWorkloadMetadata('', None)

  def testWorkloadMetadataGCEMetadata(self):
    self._testWorkloadMetadata(
        '--workload-metadata=gce_metadata',
        self.messages.WorkloadMetadataConfig(
            mode=self.messages.WorkloadMetadataConfig.\
                ModeValueValuesEnum.GCE_METADATA))
    self._testWorkloadMetadata(
        '--workload-metadata-from-node=gce_metadata',
        self.messages.WorkloadMetadataConfig(
            mode=self.messages.WorkloadMetadataConfig.\
                ModeValueValuesEnum.GCE_METADATA))

  def testWorkloadMetadataGKEMetadata(self):
    self._testWorkloadMetadata(
        '--workload-metadata=gke_metadata',
        self.messages.WorkloadMetadataConfig(
            mode=self.messages.WorkloadMetadataConfig.\
                ModeValueValuesEnum.GKE_METADATA))
    self._testWorkloadMetadata(
        '--workload-metadata-from-node=gke_metadata',
        self.messages.WorkloadMetadataConfig(
            mode=self.messages.WorkloadMetadataConfig.\
                ModeValueValuesEnum.GKE_METADATA))

  def testWorkloadMetadataUnspecified(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('{base} create {name} {flags} '
               '--cluster {clusterName}'.format(
                   base=self.node_pools_command_base.format(self.ZONE),
                   name=self.NODE_POOL_NAME,
                   flags='--workload-metadata=mode_unspecified',
                   clusterName=self.CLUSTER_NAME))
      self.AssertErrContains('Invalid choice')
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('{base} create {name} {flags} '
               '--cluster {clusterName}'.format(
                   base=self.node_pools_command_base.format(self.ZONE),
                   name=self.NODE_POOL_NAME,
                   flags='--workload-metadata_from_node=mode_unspecified',
                   clusterName=self.CLUSTER_NAME))
      self.AssertErrContains('Invalid choice')

  def testCreateInvalidSandboxConfig(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.node_pools_command_base.format(self.ZONE) +
          ' create {0} --cluster={1} --sandbox '
          'type={2}'.format(self.NODE_POOL_NAME, self.CLUSTER_NAME, 'notatype'))
    self.AssertErrContains('argument --sandbox')

  def testCreateEmptySandboxConfig(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.node_pools_command_base.format(self.ZONE) +
          ' create {0} --cluster={1} --sandbox'.format(self.NODE_POOL_NAME,
                                                       self.CLUSTER_NAME))
    self.AssertErrContains('argument --sandbox')

  def testCreateNonemptySandboxWithNoType(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.node_pools_command_base.format(self.ZONE) +
          ' create {0} --cluster={1} --sandbox '
          'foo={2}'.format(self.NODE_POOL_NAME, self.CLUSTER_NAME, 'bar'))
    self.AssertErrContains('argument --sandbox')

  def testEnableSurgeUpgrade(self):
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                  self.PROJECT_ID))
    pool_kwargs = {
        'name':
            'my-custom-pool',
        'clusterId':
            self.CLUSTER_NAME,
        'upgradeSettings':
            self._MakeUpgradeSettings(maxSurge=3, maxUnavailable=2),
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
        self.node_pools_command_base.format(self.ZONE) +
        ' create {name} --cluster={clusterId}'
        ' --max-surge-upgrade=3 --max-unavailable-upgrade=2'.format(
            **pool_kwargs))
    self.AssertOutputEquals(
        ('NAME MACHINE_TYPE DISK_SIZE_GB NODE_VERSION\n'
         '{name} {version}\n').format(name=pool.name, version=pool.version),
        normalize_space=True)


class CreateTestGAOnly(CreateTestGA):
  """gcloud GA track only using container v1 API (not beta/alpha)."""


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class CreateTestBeta(base.BetaTestBase, CreateTestGA):
  """gcloud Beta track using container v1beta1 API."""

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
            m.WorkloadMetadataConfig(nodeMetadata=m.WorkloadMetadataConfig
                                     .NodeMetadataValueValuesEnum.SECURE),
        'bootDiskKmsKey':
            'projects/bing/locations/baz/keyRings/bar/cryptoKeys/foo',
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
        ' --workload-metadata-from-node=secure'
        ' --boot-disk-kms-key={bootDiskKmsKey}'.format(**pool_kwargs))
    self.AssertOutputEquals(
        ('NAME MACHINE_TYPE DISK_SIZE_GB NODE_VERSION\n'
         '{name} {version}\n').format(name=pool.name, version=pool.version),
        normalize_space=True)

  def testWorkloadMetadataSecure(self):
    self._testWorkloadMetadata(
        '--workload-metadata-from-node=secure',
        self.messages.WorkloadMetadataConfig(
            nodeMetadata=self.messages.WorkloadMetadataConfig.\
                NodeMetadataValueValuesEnum.SECURE))

  def testWorkloadMetadataExpose(self):
    self._testWorkloadMetadata(
        '--workload-metadata-from-node=exposed',
        self.messages.WorkloadMetadataConfig(
            nodeMetadata=self.messages.WorkloadMetadataConfig.\
                NodeMetadataValueValuesEnum.EXPOSE))

  def testWorkloadMetadataGKEMetadataServer(self):
    self._testWorkloadMetadata(
        '--workload-metadata-from-node=gke_metadata_server',
        self.messages.WorkloadMetadataConfig(
            nodeMetadata=self.messages.WorkloadMetadataConfig.\
                NodeMetadataValueValuesEnum.GKE_METADATA_SERVER))

  def testWorkloadMetadataUnspecified(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('{base} create {name} {flags} '
               '--cluster {clusterName}'.format(
                   base=self.node_pools_command_base.format(self.ZONE),
                   name=self.NODE_POOL_NAME,
                   flags='--workload-metadata=unspecified',
                   clusterName=self.CLUSTER_NAME))
      self.AssertErrContains('Invalid choice')
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('{base} create {name} {flags} '
               '--cluster {clusterName}'.format(
                   base=self.node_pools_command_base.format(self.ZONE),
                   name=self.NODE_POOL_NAME,
                   flags='--workload-metadata-from-node=unspecified',
                   clusterName=self.CLUSTER_NAME))
      self.AssertErrContains('Invalid choice')

  def _testNodeLocations(self, flags, locations):
    pool_kwargs = {'nodePoolLocations': locations}
    expected_pool, return_pool = self.makeExpectedAndReturnNodePools(
        pool_kwargs)
    # Create node pool expects node pool and returns pending operation.
    self.ExpectCreateNodePool(expected_pool, self._MakeNodePoolOperation())
    # Get operation returns done operation.
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    # Get returns expected node pool, populated with other fields by server.
    self.ExpectGetNodePool(return_pool.name, response=return_pool)
    self.Run('{base} create {name} {flags} '
             '--cluster {clusterName}'.format(
                 base=self.node_pools_command_base.format(self.ZONE),
                 name=self.NODE_POOL_NAME,
                 flags=flags,
                 clusterName=self.CLUSTER_NAME))

  def testNodeLocations(self):
    self._testNodeLocations(
        '--node-locations=us-central1-a,us-central1-b',
        locations=['us-central1-a', 'us-central1-b'])

  def testWarnNodeVersionWithAutoUpgradeEnabled(self):
    pool_kwargs = {
        'nodeVersion':
            self.VERSION,
        'management':
            self.messages.NodeManagement(autoRepair=True, autoUpgrade=True)
    }
    expected_pool, return_pool = self.makeExpectedAndReturnNodePools(
        pool_kwargs)
    self.ExpectCreateNodePool(expected_pool, self._MakeNodePoolOperation())
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.ExpectGetNodePool(return_pool.name, response=return_pool)
    self.Run('{base} create {name} --cluster {clusterName} '
             '--node-version {version} --quiet'.format(
                 base=self.node_pools_command_base.format(self.ZONE),
                 name=self.NODE_POOL_NAME,
                 clusterName=self.CLUSTER_NAME,
                 version=self.VERSION))
    self.AssertErrContains(c_util.WARN_NODE_VERSION_WITH_AUTOUPGRADE_ENABLED)

  @parameterized.parameters('--max-surge-upgrade=2',
                            '--max-unavailable-upgrade=1')
  def testInvalidSurgeUpgrade(self, upgrade_flag):
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                  self.PROJECT_ID))
    pool_kwargs = {
        'name': 'my-custom-pool',
        'clusterId': self.CLUSTER_NAME,
        'upgradeFlag': upgrade_flag,
    }
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run(
          self.node_pools_command_base.format(self.ZONE) +
          ' create {name} --cluster={clusterId} {upgradeFlag}'.format(
              **pool_kwargs))
    self.AssertErrContains(c_util.INVALIID_SURGE_UPGRADE_SETTINGS)


# Mixin class must come in first to have the correct multi-inheritance behavior.
class CreateTestAlpha(base.AlphaTestBase, CreateTestBeta):
  """gcloud Alpha track using container v1alpha1 API."""

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
            m.WorkloadMetadataConfig(nodeMetadata=m.WorkloadMetadataConfig
                                     .NodeMetadataValueValuesEnum.SECURE),
        'localSsdVolumeConfigs': [
            m.LocalSsdVolumeConfig(count=2, type='nvme', format=format_enum.FS),
            m.LocalSsdVolumeConfig(
                count=1, type='scsi', format=format_enum.BLOCK),
        ],
        'bootDiskKmsKey':
            'projects/bing/locations/baz/keyRings/bar/cryptoKeys/foo',
        'nodeGroup':
            'test-node-group',
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
        ' --boot-disk-kms-key={bootDiskKmsKey}'
        ' --local-ssd-volumes count=2,type=nvme,format=fs'
        ' --local-ssd-volumes count=1,type=scsi,format=block'
        ' --workload-metadata-from-node=secure'
        ' --node-group {nodeGroup}'.format(**pool_kwargs))
    self.AssertOutputEquals(
        ('NAME MACHINE_TYPE DISK_SIZE_GB NODE_VERSION\n'
         '{name} {version}\n').format(name=pool.name, version=pool.version),
        normalize_space=True)

  @parameterized.parameters((1, 'notatype', 'fs'), (4, 'scsi', 'notaformat'),
                            ('notacount', 'scsi', 'fs'), (0, 'scsi', 'fs'))
  def testCreateInvalidLocalSsdVolumeConfig(self, ssd_count, ssd_type,
                                            ssd_format):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.node_pools_command_base.format(self.ZONE) +
          ' create {0} --cluster={1} --local-ssd-volumes '
          'count={2},type={3},format={4}'.format(
              self.NODE_POOL_NAME, self.CLUSTER_NAME, ssd_count, ssd_type,
              ssd_format))
    self.AssertErrContains('argument --local-ssd-volumes')

  def testCreateEmptyLocalSsdVolumeConfig(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(
          self.node_pools_command_base.format(self.ZONE) +
          ' create {0} --cluster={1} --local-ssd-volumes'.format(
              self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.AssertErrContains('argument --local-ssd-volumes')

  def testLinuxSysctlConfig(self):
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                  self.PROJECT_ID))
    pool_kwargs = {
        'name':
            'my-custom-pool',
        'clusterId':
            self.CLUSTER_NAME,
        'linuxNodeConfig':
            self.msgs.LinuxNodeConfig(
                sysctls=self.msgs.LinuxNodeConfig
                .SysctlsValue(additionalProperties=[
                    self.msgs.LinuxNodeConfig.SysctlsValue.AdditionalProperty(
                        key='net.core.somaxconn', value='4096'),
                    self.msgs.LinuxNodeConfig.SysctlsValue.AdditionalProperty(
                        key='net.ipv4.tcp_rmem', value='4096 87380 6291456'),
                ])),
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
        ' --linux-sysctls="net.core.somaxconn=4096,'
        'net.ipv4.tcp_rmem=4096 87380 6291456"'.format(**pool_kwargs))
    self.AssertOutputEquals(
        ('NAME MACHINE_TYPE DISK_SIZE_GB NODE_VERSION\n'
         '{name} {version}\n').format(name=pool.name, version=pool.version),
        normalize_space=True)

  def testShieldedInstanceConfig(self):
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                  self.PROJECT_ID))
    pool_kwargs = {
        'name':
            'my-custom-pool',
        'clusterId':
            self.CLUSTER_NAME,
        'shieldedInstanceConfig':
            self.messages.ShieldedInstanceConfig(
                enableSecureBoot=True, enableIntegrityMonitoring=False),
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

    self.Run('{node_pools_command_base} create {name}'
             ' --cluster={clusterId}'
             ' --shielded-secure-boot'
             ' --no-shielded-integrity-monitoring'.format(
                 node_pools_command_base=self.node_pools_command_base.format(
                     self.ZONE),
                 **pool_kwargs))
    self.AssertOutputEquals(
        ('NAME MACHINE_TYPE DISK_SIZE_GB NODE_VERSION\n'
         '{name} {version}\n').format(name=pool.name, version=pool.version),
        normalize_space=True)

  def testNodeConfigFromFile(self):
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                  self.PROJECT_ID))
    pool_kwargs = {
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

    self.ExpectCreateNodePool(
        self._MakeNodePool(**pool_kwargs),
        self._MakeNodePoolOperation(**pool_kwargs))

    self.ExpectGetOperation(
        self._MakeNodePoolOperation(status=self.op_done, **pool_kwargs))

    pool_version_kwargs = pool_kwargs.copy()
    pool_version_kwargs.update({'nodeVersion': self.VERSION})
    pool = self._MakeNodePool(**pool_version_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool)

    node_config = self.Touch(
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
        self.node_pools_command_base.format(self.ZONE) + ' create {name}'
        ' --cluster={cluster_id}'
        ' --node-config={node_config}'.format(
            name='my-pool',
            cluster_id=self.CLUSTER_NAME,
            node_config=node_config))
    self.AssertOutputEquals(
        ('NAME MACHINE_TYPE DISK_SIZE_GB NODE_VERSION\n'
         '{name} {version}\n').format(name=pool.name, version=pool.version),
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
