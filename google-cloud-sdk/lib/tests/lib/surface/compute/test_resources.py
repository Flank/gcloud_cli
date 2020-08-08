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
"""Resources that are shared by two or more tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis

alpha_messages = core_apis.GetMessagesModule('compute', 'alpha')
beta_messages = core_apis.GetMessagesModule('compute', 'beta')
messages = core_apis.GetMessagesModule('compute', 'v1')

_COMPUTE_PATH = 'https://compute.googleapis.com/compute'

_V1_URI_PREFIX = _COMPUTE_PATH + '/v1/projects/my-project/'
_ALPHA_URI_PREFIX = _COMPUTE_PATH + '/alpha/projects/my-project/'
_BETA_URI_PREFIX = _COMPUTE_PATH + '/beta/projects/my-project/'


# TODO(b/35952682): Convert all the fixtures here to use this common method.
def _GetMessagesForApi(api):
  if api == 'alpha':
    return alpha_messages
  elif api == 'beta':
    return beta_messages
  elif api == 'v1':
    return messages
  else:
    assert False


ADDRESSES = [
    messages.Address(
        address='23.251.134.124',
        name='address-1',
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/region-1'),
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'regions/region-1/addresses/address-1'),
        status=messages.Address.StatusValueValuesEnum.IN_USE),

    messages.Address(
        address='23.251.134.125',
        name='address-2',
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/region-1'),
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'regions/region-1/addresses/address-2'),
        status=messages.Address.StatusValueValuesEnum.RESERVED),
]



GLOBAL_ADDRESSES = [
    messages.Address(
        address='23.251.134.126',
        name='global-address-1',
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'global/addresses/global-address-1'),
        status=messages.Address.StatusValueValuesEnum.IN_USE),

    messages.Address(
        address='23.251.134.127',
        name='global-address-2',
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'global/addresses/global-address-2'),
        status=messages.Address.StatusValueValuesEnum.RESERVED),
]


CENTOS_IMAGES = [
    messages.Image(
        name='centos-6-v20140408',
        family='centos-6',
        selfLink=('https://compute.googleapis.com/compute/v1/projects/centos-cloud/'
                  'global/images/centos-6-v20140408'),
        status=messages.Image.StatusValueValuesEnum.READY),

    messages.Image(
        name='centos-6-v20140318',
        family='centos-6',
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.DEPRECATED),
        selfLink=('https://compute.googleapis.com/compute/v1/projects/centos-cloud/'
                  'global/images/centos-6-v20140318'),
        status=messages.Image.StatusValueValuesEnum.READY),
]


def MakeDiskTypes(msgs, api, scope_type='zone', scope_name='zone-1',
                  project='my-project'):
  """Creates a list of diskType messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.
    scope_type: The type of scope (zone or region)
    scope_name: The name of scope (eg. us-central1-a)
    project: The project name.

  Returns:
    A list of message objects representing diskTypes.
  """

  if api is None:
    api = 'v1'
  prefix = '{0}/{1}'.format(_COMPUTE_PATH, api)
  disk_types = [
      msgs.DiskType(
          name='pd-standard',
          validDiskSize='10GB-10TB',
          selfLink=('{0}/projects/{1}/{2}/{3}/diskTypes/pd-standard'
                    .format(prefix, project, scope_type + 's', scope_name)),
      ),
      msgs.DiskType(
          deprecated=msgs.DeprecationStatus(
              state=msgs.DeprecationStatus.StateValueValuesEnum.OBSOLETE),
          name='pd-ssd',
          validDiskSize='10GB-1TB',
          selfLink=('{0}/projects/{1}/{2}/{3}/diskTypes/pd-ssd'
                    .format(prefix, project, scope_type + 's', scope_name))),
  ]
  for disk_type in disk_types:
    # Field 'region' is missing in regional disk types.
    if scope_type == 'zone':
      setattr(disk_type, scope_type,
              '{0}/projects/{1}/{2}/{3}'
              .format(prefix, project, scope_type + 's', scope_name))
  return disk_types

DISK_TYPES = [
    messages.DiskType(
        name='pd-standard',
        validDiskSize='10GB-10TB',
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/diskTypes/pd-standard'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),

    messages.DiskType(
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.OBSOLETE),
        name='pd-ssd',
        validDiskSize='10GB-1TB',
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/diskTypes/pd-ssd'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),

]

DISKS = [
    messages.Disk(
        name='disk-1',
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/disks/disk-1'),
        sizeGb=10,
        status=messages.Disk.StatusValueValuesEnum.READY,
        type=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-1/diskTypes/pd-ssd'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),

    messages.Disk(
        name='disk-2',
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/disks/disk-2'),
        sizeGb=10,
        status=messages.Disk.StatusValueValuesEnum.READY,
        type=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-1/diskTypes/pd-ssd'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),

    messages.Disk(
        name='disk-3',
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/disks/disk-3'),
        sizeGb=10,
        status=messages.Disk.StatusValueValuesEnum.READY,
        type=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-1/diskTypes/pd-standard'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),
]


def MakeIamPolicy(msgs, etag, bindings=None):
  if bindings:
    return msgs.Policy(etag=etag, bindings=bindings)
  else:
    return msgs.Policy(etag=etag)


def EmptyIamPolicy(msgs):
  return MakeIamPolicy(msgs, b'test')


def IamPolicyWithOneBinding(msgs):
  return MakeIamPolicy(msgs, b'test',
                       bindings=[msgs.Binding(
                           role='owner',
                           members=['user:testuser@google.com'])])


def IamPolicyWithOneBindingAndDifferentEtag(msgs):
  return MakeIamPolicy(msgs, b'etagTwo',
                       bindings=[msgs.Binding(
                           role='owner',
                           members=['user:testuser@google.com'])])



IMAGES = [
    messages.Image(
        name='image-1',
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'global/images/image-1'),
        status=messages.Image.StatusValueValuesEnum.READY),

    messages.Image(
        name='image-2',
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'global/images/image-2'),
        status=messages.Image.StatusValueValuesEnum.READY),

    messages.Image(
        name='image-3',
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.DEPRECATED),
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'global/images/image-3'),
        status=messages.Image.StatusValueValuesEnum.READY),

    messages.Image(
        name='image-4',
        deprecated=messages.DeprecationStatus(
            deprecated='2019-04-01T15:00:00'),
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'global/images/image-4'),
        status=messages.Image.StatusValueValuesEnum.READY),
]


MACHINE_TYPES = [
    messages.MachineType(
        name='n1-standard-1',
        guestCpus=1,
        memoryMb=3840,
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/machineTypes/n1-standard-1'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),

    messages.MachineType(
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.OBSOLETE),
        name='n1-standard-1-d',
        guestCpus=1,
        memoryMb=3840,
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/machineTypes/n1-standard-1-d'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),

    messages.MachineType(
        name='n1-highmem-2',
        guestCpus=2,
        memoryMb=30720,
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/machineTypes/n1-standard-2'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),
]


def MakeMachineImages(msgs, api):
  """Creates a set of Machine Image messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the machine images.

  Returns:
    A list of message objects representing machine images.
  """
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.MachineImage(
          name='machine-image-1',
          description='Machine Image 1',
          status=msgs.MachineImage.StatusValueValuesEnum.READY,
          selfLink=(prefix + '/projects/my-project/'
                    'global/machineImages/machine-image-1'),
          sourceInstanceProperties=msgs.SourceInstanceProperties(
              machineType='n1-standard-1',
              disks=[
                  msgs.SavedAttachedDisk(
                      autoDelete=True,
                      boot=True,
                      deviceName='device-1',
                      mode=(msgs.SavedAttachedDisk.
                            ModeValueValuesEnum.READ_WRITE),
                      source='disk-1',
                      type=(msgs.SavedAttachedDisk.
                            TypeValueValuesEnum.PERSISTENT),
                  ),
                  msgs.SavedAttachedDisk(
                      autoDelete=True,
                      boot=True,
                      deviceName='device-2',
                      mode=(msgs.SavedAttachedDisk.
                            ModeValueValuesEnum.READ_ONLY),
                      type=(msgs.SavedAttachedDisk.
                            TypeValueValuesEnum.SCRATCH),
                  ),
              ])),

      msgs.MachineImage(
          name='machine-image-2',
          description='Machine Image 2',
          status=msgs.MachineImage.StatusValueValuesEnum.CREATING,
          selfLink=(prefix + '/projects/my-project/'
                    'global/machineImages/machine-image-2')),
  ]


MACHINE_IMAGES_ALPHA = MakeMachineImages(alpha_messages, 'alpha')
MACHINE_IMAGES = MACHINE_IMAGES_ALPHA


NETWORKS_V1 = [
    # Legacy
    messages.Network(
        name='network-1',
        gatewayIPv4='10.240.0.1',
        IPv4Range='10.240.0.0/16',
        routingConfig=messages.NetworkRoutingConfig(routingMode=(
            messages.NetworkRoutingConfig.RoutingModeValueValuesEnum.REGIONAL)),
        selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                  'my-project/global/networks/network-1')),

    # Custom
    messages.Network(
        name='network-2',
        autoCreateSubnetworks=False,
        routingConfig=messages.NetworkRoutingConfig(routingMode=(
            messages.NetworkRoutingConfig.RoutingModeValueValuesEnum.REGIONAL)),
        selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                  'my-project/global/networks/network-2'),
        subnetworks=[
            'https://compute.googleapis.com/compute/v1/projects/'
            'my-project/regions/region-1/subnetworks/subnetwork-1',
            'https://compute.googleapis.com/compute/v1/projects/'
            'my-project/regions/region-1/subnetworks/subnetwork-2'
        ]),

    # Auto
    messages.Network(
        name='network-3',
        autoCreateSubnetworks=True,
        routingConfig=messages.NetworkRoutingConfig(routingMode=(
            messages.NetworkRoutingConfig.RoutingModeValueValuesEnum.GLOBAL)),
        selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                  'my-project/global/networks/network-3'),
        subnetworks=[])
]

NETWORK_PEERINGS_V1 = [
    messages.Network(
        name='network-1',
        autoCreateSubnetworks=True,
        selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                  'my-project/global/networks/network-1'),
        subnetworks=[],
        peerings=[
            messages.NetworkPeering(
                autoCreateRoutes=True,
                name='peering-1',
                network='https://compute.googleapis.com/compute/v1/'
                'projects/my-project/global/networks/network-2',
                state=messages.NetworkPeering.StateValueValuesEnum.ACTIVE,
                stateDetails='Matching configuration is found on peer network.'
            ),
            messages.NetworkPeering(
                autoCreateRoutes=True,
                name='peering-2',
                network='https://compute.googleapis.com/compute/v1/'
                'projects/my-project-2/global/networks/network-3',
                state=messages.NetworkPeering.StateValueValuesEnum.ACTIVE,
                stateDetails='Matching configuration is found on peer '
                'network.'),
            messages.NetworkPeering(
                autoCreateRoutes=True,
                name='peering-3',
                network='https://compute.googleapis.com/compute/v1/'
                'projects/my-project-3/global/networks/network-3',
                state=(messages.NetworkPeering.StateValueValuesEnum.INACTIVE),
                stateDetails='Peering is created.')
        ]),
    messages.Network(
        name='network-2',
        autoCreateSubnetworks=True,
        selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                  'my-project/global/networks/network-2'),
        subnetworks=[],
        peerings=[
            messages.NetworkPeering(
                autoCreateRoutes=True,
                name='my-peering-1',
                network='https://compute.googleapis.com/compute/v1/projects/'
                'my-project/global/networks/network-1',
                state=messages.NetworkPeering.StateValueValuesEnum.ACTIVE,
                stateDetails='Matching configuration is found on peer network.')
        ])
]


def MakeNodesInNodeGroup(msgs, api):
  prefix = '{0}/{1}/'.format(_COMPUTE_PATH, api)
  return [
      msgs.NodeGroupNode(
          name='node-1',
          status=msgs.NodeGroupNode.StatusValueValuesEnum.READY,
          instances=[
              prefix + '/projects/my-project/zones/zone-1/'
              'instances/instance-1',
              prefix + '/projects/my-project/zones/zone-1/'
              'instances/instance-2'
          ],
          nodeType=prefix +
          '/projects/my-project/zones/zone-1/nodeTypes/iAPX-286',
          serverId='server-1'),
      msgs.NodeGroupNode(
          name='node-2',
          status=msgs.NodeGroupNode.StatusValueValuesEnum.READY,
          instances=[
              prefix + '/projects/my-project/zones/zone-1/'
              'instances/instance-3'
          ],
          nodeType=prefix +
          '/projects/my-project/zones/zone-1/nodeTypes/iAPX-286',
          serverId='server-2')
  ]


def MakeNodeGroups(msgs, api):
  """Creates a set of Node Group messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.

  Returns:
    A list of message objects representing sole tenancy note groups.
  """
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.NodeGroup(
          creationTimestamp='2018-01-23T10:00:00.0Z',
          description='description1',
          kind='compute#nodeGroup',
          name='group-1',
          nodeTemplate=(prefix + '/projects/my-project/'
                        'regions/region-1/nodeTemplates/template-1'),
          size=2,
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/nodeGroups/group-1'),
          zone='zone-1'),
      msgs.NodeGroup(
          creationTimestamp='2018-02-21T10:00:00.0Z',
          description='description2',
          kind='compute#nodeGroup',
          name='group-2',
          nodeTemplate=(prefix + '/projects/my-project/'
                        'regions/region-1/nodeTemplates/template-2'),
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/nodeGroups/group-2'),
          size=1,
          zone='zone-1'),
  ]


NODE_GROUPS = MakeNodeGroups(messages, 'v1')


def MakeNodeTemplates(msgs, api):
  """Creates a set of Node Template messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.

  Returns:
    A list of message objects representing sole tenancy note templates.
  """
  prefix = _COMPUTE_PATH + '/' + api
  node_affinity_value = msgs.NodeTemplate.NodeAffinityLabelsValue
  return [
      msgs.NodeTemplate(
          creationTimestamp='2017-12-12T10:00:00.0Z',
          description='a cool template',
          kind='compute#nodeTemplate',
          name='template-1',
          nodeAffinityLabels=node_affinity_value(
              additionalProperties=[
                  node_affinity_value.AdditionalProperty(
                      key='environment', value='prod'),
                  node_affinity_value.AdditionalProperty(
                      key='nodeGrouping', value='frontend')]),
          nodeType='iAPX-286',
          region=(prefix + '/projects/my-project/regions/region-1'),
          selfLink=(prefix + '/projects/my-project/'
                    'regions/region-1/nodeTemplates/template-1'),
          status=msgs.NodeTemplate.StatusValueValuesEnum.READY,
          statusMessage='Template is ready.'),
      msgs.NodeTemplate(
          creationTimestamp='2018-01-15T10:00:00.0Z',
          description='a cold template',
          kind='compute#nodeTemplate',
          name='template-2',
          nodeAffinityLabels=node_affinity_value(
              additionalProperties=[
                  node_affinity_value.AdditionalProperty(
                      key='environment', value='prod'),
                  node_affinity_value.AdditionalProperty(
                      key='nodeGrouping', value='backend')]),
          nodeType='n1-node-96-624',
          region=(prefix + '/projects/my-project/regions/region-1'),
          selfLink=(prefix + '/projects/my-project/'
                    'regions/region-1/nodeTemplates/template-2'),
          status=msgs.NodeTemplate.StatusValueValuesEnum.CREATING,
          statusMessage='Template is being created.'),
  ]


NODE_TEMPLATES = MakeNodeTemplates(messages, 'v1')


def MakeNodeTypes(msgs, api):
  """Creates a set of Node Type messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.

  Returns:
    A list of message objects representing sole tenancy node types.
  """
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.NodeType(
          cpuPlatform='80286',
          creationTimestamp='1982-02-01T10:00:00.0Z',
          deprecated=msgs.DeprecationStatus(
              state=msgs.DeprecationStatus.StateValueValuesEnum.OBSOLETE),
          description='oldie but goodie',
          guestCpus=1,
          id=159265359,
          kind='compute#nodeType',
          localSsdGb=0,
          memoryMb=256,
          name='iAPX-286',
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/nodeTypes/iAPX-286'),
          zone='zone-1'),
      msgs.NodeType(
          cpuPlatform='skylake',
          creationTimestamp='2014-12-12T10:00:00.0Z',
          description='',
          guestCpus=96,
          id=159265360,
          kind='compute#nodeType',
          localSsdGb=0,
          memoryMb=416000,
          name='n1-node-96-624',
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/nodeTypes/n1-node-96-624'),
          zone='zone-1'),
  ]


NODE_TYPES = MakeNodeTypes(messages, 'v1')


def MakeOsloginClient(version, use_extended_profile=False):
  """Return a dummy oslogin API client."""
  oslogin_messages = core_apis.GetMessagesModule('oslogin', version)

  ssh_public_keys_value = oslogin_messages.LoginProfile.SshPublicKeysValue
  profile_basic = oslogin_messages.LoginProfile(
      name='user@google.com',
      posixAccounts=[oslogin_messages.PosixAccount(
          primary=True,
          username='user_google_com',
          uid=123456,
          gid=123456,
          homeDirectory='/home/user_google_com',
          shell='/bin/bash')],
      sshPublicKeys=ssh_public_keys_value(
          additionalProperties=[
              ssh_public_keys_value.AdditionalProperty(
                  key='qwertyuiop',
                  value=oslogin_messages.SshPublicKey(
                      fingerprint=b'asdfasdf',
                      key='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCks0aWrx'))]),
  )

  profile_extended = oslogin_messages.LoginProfile(
      name='user@google.com',
      posixAccounts=[
          oslogin_messages.PosixAccount(
              primary=False,
              username='user_google_com',
              uid=123456,
              gid=123456,
              homeDirectory='/home/user_google_com',
              shell='/bin/bash'),
          oslogin_messages.PosixAccount(
              primary=False,
              username='testaccount',
              uid=123456,
              gid=123456,
              homeDirectory='/home/testaccount',
              shell='/bin/bash'),
          oslogin_messages.PosixAccount(
              primary=True,
              username='myaccount',
              uid=123456,
              gid=123456,
              homeDirectory='/home/myaccount',
              shell='/bin/bash'),
      ],
      sshPublicKeys=ssh_public_keys_value(
          additionalProperties=[
              ssh_public_keys_value.AdditionalProperty(
                  key='qwertyuiop',
                  value=oslogin_messages.SshPublicKey(
                      fingerprint=b'asdfasdf',
                      key='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCks0aWrx'))]),
  )

  if use_extended_profile:
    login_profile = profile_extended
  else:
    login_profile = profile_basic

  import_public_key_response = oslogin_messages.ImportSshPublicKeyResponse(
      loginProfile=login_profile)

  class _OsloginUsers(object):
    """Mock OS Login Users class."""

    @classmethod
    def ImportSshPublicKey(cls, message):
      del cls, message  # Unused
      return import_public_key_response

    @classmethod
    def GetLoginProfile(cls, message):
      del cls, message  # Unused
      return login_profile

  class _OsloginClient(object):
    users = _OsloginUsers
    MESSAGES_MODULE = oslogin_messages

  return _OsloginClient()


PROJECTS = [
    messages.Project(
        name='my-project',
        creationTimestamp='2013-09-06T17:54:10.636-07:00',
        commonInstanceMetadata=messages.Metadata(
            items=[
                messages.Metadata.ItemsValueListEntry(
                    key='a',
                    value='b'),
                messages.Metadata.ItemsValueListEntry(
                    key='c',
                    value='d'),
            ]
        ),
        selfLink='https://compute.googleapis.com/compute/v1/projects/my-project/')
]


REGIONS = [
    messages.Region(
        name='region-1',
        quotas=[
            messages.Quota(
                limit=24.0,
                metric=messages.Quota.MetricValueValuesEnum.CPUS,
                usage=0.0),
            messages.Quota(
                limit=5120.0,
                metric=messages.Quota.MetricValueValuesEnum.DISKS_TOTAL_GB,
                usage=30.0),
            messages.Quota(
                limit=7.0,
                metric=messages.Quota.MetricValueValuesEnum.STATIC_ADDRESSES,
                usage=1.0),
            messages.Quota(
                limit=24.0,
                metric=messages.Quota.MetricValueValuesEnum.IN_USE_ADDRESSES,
                usage=2.0),
        ],
        status=messages.Region.StatusValueValuesEnum.UP,
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'regions/region-1'),
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.DEPRECATED,
            deleted='2015-03-29T00:00:00.000-07:00',
            replacement=('https://compute.googleapis.com/compute/v1/projects/'
                         'my-project/regions/region-2'))),

    messages.Region(
        name='region-2',
        quotas=[
            messages.Quota(
                limit=240.0,
                metric=messages.Quota.MetricValueValuesEnum.CPUS,
                usage=0.0),
            messages.Quota(
                limit=51200.0,
                metric=messages.Quota.MetricValueValuesEnum.DISKS_TOTAL_GB,
                usage=300.0),
            messages.Quota(
                limit=70.0,
                metric=messages.Quota.MetricValueValuesEnum.STATIC_ADDRESSES,
                usage=10.0),
            messages.Quota(
                limit=240.0,
                metric=messages.Quota.MetricValueValuesEnum.IN_USE_ADDRESSES,
                usage=20.0),
        ],
        status=messages.Region.StatusValueValuesEnum.UP,
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'regions/region-2')),

    messages.Region(
        name='region-3',
        quotas=[
            messages.Quota(
                limit=4800.0,
                metric=messages.Quota.MetricValueValuesEnum.CPUS,
                usage=2000.0),
            messages.Quota(
                limit=102400.0,
                metric=messages.Quota.MetricValueValuesEnum.DISKS_TOTAL_GB,
                usage=600.0),
            messages.Quota(
                limit=140.0,
                metric=messages.Quota.MetricValueValuesEnum.STATIC_ADDRESSES,
                usage=20.0),
            messages.Quota(
                limit=480.0,
                metric=messages.Quota.MetricValueValuesEnum.IN_USE_ADDRESSES,
                usage=40.0),
        ],
        status=messages.Region.StatusValueValuesEnum.UP,
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'regions/region-3')),
]


BETA_REGIONS = [
    beta_messages.Region(
        name='region-1',
        quotas=[
            beta_messages.Quota(
                limit=24.0,
                metric=beta_messages.Quota.MetricValueValuesEnum.CPUS,
                usage=0.0),
            beta_messages.Quota(
                limit=5120.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .DISKS_TOTAL_GB,
                usage=30.0),
            beta_messages.Quota(
                limit=7.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .STATIC_ADDRESSES,
                usage=1.0),
            beta_messages.Quota(
                limit=24.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .IN_USE_ADDRESSES,
                usage=2.0)],
        status=beta_messages.Region.StatusValueValuesEnum.UP,
        selfLink=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'regions/region-1'),
        deprecated=beta_messages.DeprecationStatus(
            state=beta_messages.DeprecationStatus.StateValueValuesEnum
            .DEPRECATED,
            deleted='2015-03-29T00:00:00.000-07:00',
            replacement=(
                'https://compute.googleapis.com/compute/beta/projects/'
                'my-project/regions/region-2'))),
    beta_messages.Region(
        name='region-2',
        quotas=[
            beta_messages.Quota(
                limit=240.0,
                metric=beta_messages.Quota.MetricValueValuesEnum.CPUS,
                usage=0.0),
            beta_messages.Quota(
                limit=51200.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .DISKS_TOTAL_GB,
                usage=300.0),
            beta_messages.Quota(
                limit=70.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .STATIC_ADDRESSES,
                usage=10.0),
            beta_messages.Quota(
                limit=240.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .IN_USE_ADDRESSES,
                usage=20.0)],
        status=beta_messages.Region.StatusValueValuesEnum.UP,
        selfLink=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'regions/region-2')),
    beta_messages.Region(
        name='region-3',
        quotas=[
            beta_messages.Quota(
                limit=4800.0,
                metric=beta_messages.Quota.MetricValueValuesEnum.CPUS,
                usage=2000.0),
            beta_messages.Quota(
                limit=102400.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .DISKS_TOTAL_GB,
                usage=600.0),
            beta_messages.Quota(
                limit=140.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .STATIC_ADDRESSES,
                usage=20.0),
            beta_messages.Quota(
                limit=480.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .IN_USE_ADDRESSES,
                usage=40.0)],
        status=beta_messages.Region.StatusValueValuesEnum.UP,
        selfLink=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'regions/region-3'))]


def MakeRoutes(msgs, api, network='default'):
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.Route(
          destRange='10.0.0.0/8',
          name='route-1',
          network=(prefix + '/projects/my-project/'
                   'network/' + network),
          nextHopIp='10.240.0.0',
          selfLink=(prefix + '/projects/my-project/'
                    'global/routes/route-1'),
      ),

      msgs.Route(
          destRange='0.0.0.0/0',
          name='route-2',
          network=(prefix + '/projects/my-project/'
                   'network/' + network),
          nextHopInstance=(
              prefix + '/projects/my-project/'
              'zones/zone-1/instances/instance-1'),
          selfLink=(prefix + '/projects/my-project/'
                    'global/routes/route-2'),
      ),

      msgs.Route(
          destRange='10.10.0.0/16',
          name='route-3',
          network=(prefix + '/projects/my-project/'
                   'network/' + network),
          nextHopGateway=(
              prefix + '/projects/my-project/'
              'global/gateways/default-internet-gateway'),
          selfLink=(prefix + '/projects/my-project/'
                    'global/routes/route-3'),
          priority=1,
      ),

      msgs.Route(
          destRange='10.10.0.0/16',
          name='route-4',
          network=(prefix + '/projects/my-project/'
                   'network/' + network),
          nextHopVpnTunnel=(
              prefix + '/projects/my-project/'
              'regions/region-1/vpnTunnels/tunnel-1'),
          selfLink=(prefix + '/projects/my-project/'
                    'global/routes/route-4'),
      ),
  ]

ROUTES_V1 = MakeRoutes(messages, 'v1')
ROUTES_V1_TWO_NETWORKS = ROUTES_V1 + MakeRoutes(messages, 'v1', network='foo')


def MakeSecurityPolicy(msgs, security_policy_ref):
  return msgs.SecurityPolicy(
      name=security_policy_ref.Name(),
      description='my description',
      id=123,
      fingerprint=b'=g\313\0305\220\f\266',
      rules=[
          msgs.SecurityPolicyRule(
              description='default rule',
              priority=2147483647,
              match=msgs.SecurityPolicyRuleMatcher(
                  versionedExpr=msgs.SecurityPolicyRuleMatcher.
                  VersionedExprValueValuesEnum('SRC_IPS_V1'),
                  config=msgs.SecurityPolicyRuleMatcherConfig(
                      srcIpRanges=['*'])),
              action='allow',
              preview=False)
      ],
      selfLink=security_policy_ref.SelfLink())


def MakeSecurityPolicyCloudArmorConfig(msgs, security_policy_ref):
  return msgs.SecurityPolicy(
      name=security_policy_ref.Name(),
      description='my description',
      id=123,
      fingerprint=b'=g\313\0305\220\f\266',
      rules=[
          msgs.SecurityPolicyRule(
              description='default rule',
              priority=2147483647,
              match=msgs.SecurityPolicyRuleMatcher(
                  versionedExpr=msgs.SecurityPolicyRuleMatcher.
                  VersionedExprValueValuesEnum('SRC_IPS_V1'),
                  config=msgs.SecurityPolicyRuleMatcherConfig(
                      srcIpRanges=['*'])),
              action='allow',
              preview=False)
      ],
      cloudArmorConfig=msgs.SecurityPolicyCloudArmorConfig(enableMl=True),
      selfLink=security_policy_ref.SelfLink())


def MakeSecurityPolicyMatchExpression(msgs, security_policy_ref):
  return msgs.SecurityPolicy(
      name=security_policy_ref.Name(),
      description='my description',
      id=123,
      fingerprint=b'=g\313\0305\220\f\266',
      rules=[
          msgs.SecurityPolicyRule(
              description='default rule',
              priority=2147483647,
              match=msgs.SecurityPolicyRuleMatcher(
                  expr=msgs.Expr(expression="origin.region_code == 'GB'"),
                  config=msgs.SecurityPolicyRuleMatcherConfig(
                      srcIpRanges=['*'])),
              action='allow',
              preview=False)
      ],
      selfLink=security_policy_ref.SelfLink())


def MakeSecurityPolicyRule(msgs):
  return msgs.SecurityPolicyRule(
      priority=1000,
      description='my rule',
      action='allow',
      match=msgs.SecurityPolicyRuleMatcher(
          versionedExpr=msgs.SecurityPolicyRuleMatcher.
          VersionedExprValueValuesEnum('SRC_IPS_V1'),
          config=msgs.SecurityPolicyRuleMatcherConfig(
              srcIpRanges=['1.1.1.1'])),
      preview=False)

SNAPSHOTS = [
    messages.Snapshot(
        diskSizeGb=10,
        name='snapshot-1',
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'global/snapshots/snapshot-1'),
        sourceDisk=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                    'zones/zone-1/disks/disk-1'),
        status=messages.Snapshot.StatusValueValuesEnum.READY),

    messages.Snapshot(
        diskSizeGb=10,
        name='snapshot-2',
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'global/snapshots/snapshot-2'),
        sourceDisk=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                    'zones/zone-1/disks/disk-2'),
        status=messages.Snapshot.StatusValueValuesEnum.READY),

    messages.Snapshot(
        diskSizeGb=10,
        name='snapshot-3',
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'global/snapshots/snapshot-3'),
        sourceDisk=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                    'zones/zone-1/disks/disk-3'),
        status=messages.Snapshot.StatusValueValuesEnum.READY),
]


def MakeInPlaceSnapshots(msgs, api):
  """Creates a set of in-place snapshots messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.

  Returns:
    A list of message objects representing in-place snapshots.
  """
  prefix = _COMPUTE_PATH + '/' + api + '/projects/my-project'
  zone_scope = prefix + '/zones/zone-1'
  region_scope = prefix + '/regions/region-1'

  return [
      alpha_messages.InPlaceSnapshot(
          diskSizeGb=10,
          name='ips-1',
          selfLink=(zone_scope + '/inPlacesnapshots/ips-1'),
          sourceDisk=(zone_scope + '/disks/disk-1'),
          status=alpha_messages.InPlaceSnapshot.StatusValueValuesEnum.READY,
          zone=zone_scope),
      alpha_messages.InPlaceSnapshot(
          diskSizeGb=10,
          name='ips-2',
          selfLink=(zone_scope + '/inPlacesnapshots/ips-2'),
          sourceDisk=(zone_scope + '/disks/disk-2'),
          status=alpha_messages.InPlaceSnapshot.StatusValueValuesEnum.READY,
          zone=zone_scope),
      alpha_messages.InPlaceSnapshot(
          diskSizeGb=10,
          name='ips-3',
          selfLink=(region_scope + '/inPlacesnapshots/ips-3'),
          sourceDisk=(region_scope + '/disks/disk-3'),
          status=alpha_messages.InPlaceSnapshot.StatusValueValuesEnum.READY,
          region=region_scope),
      alpha_messages.InPlaceSnapshot(
          diskSizeGb=10,
          name='ips-4',
          selfLink=(region_scope + '/inPlacesnapshots/ips-4'),
          sourceDisk=(region_scope + '/disks/disk-4'),
          status=alpha_messages.InPlaceSnapshot.StatusValueValuesEnum.READY,
          region=region_scope),
  ]


IN_PLACE_SNAPSHOT_V1 = MakeInPlaceSnapshots(messages, 'v1')
IN_PLACE_SNAPSHOT_BETA = MakeInPlaceSnapshots(beta_messages, 'beta')
IN_PLACE_SNAPSHOT_ALPHA = MakeInPlaceSnapshots(alpha_messages, 'alpha')


def MakeSslCertificates(msgs, api):
  """Make ssl Certificate test resources for the given api version."""
  prefix = _COMPUTE_PATH + '/' + api + '/projects/my-project/'
  return [
      msgs.SslCertificate(
          type=msgs.SslCertificate.TypeValueValuesEnum.SELF_MANAGED,
          name='ssl-cert-1',
          selfManaged=msgs.SslCertificateSelfManagedSslCertificate(
              certificate=textwrap.dedent("""\
                -----BEGIN CERTIFICATE-----
                MIICZzCCAdACCQDjYQHCnQOiTDANBgkqhkiG9w0BAQsFADB4MQswCQYDVQQGEwJV
                UzETMBEGA1UECAwKV2FzaGluZ3RvbjEQMA4GA1UEBwwHU2VhdHRsZTEPMA0GA1UE
                CgwGR29vZ2xlMRgwFgYDVQQLDA9DbG91ZCBQbGF0Zm9ybXMxFzAVBgNVBAMMDmdj
                bG91ZCBjb21wdXRlMB4XDTE0MTAxMzIwMTcxMloXDTE1MTAxMzIwMTcxMloweDEL
                MAkGA1UEBhMCVVMxEzARBgNVBAgMCldhc2hpbmd0b24xEDAOBgNVBAcMB1NlYXR0
                bGUxDzANBgNVBAoMBkdvb2dsZTEYMBYGA1UECwwPQ2xvdWQgUGxhdGZvcm1zMRcw
                FQYDVQQDDA5nY2xvdWQgY29tcHV0ZTCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkC
                gYEAw3JXUCTn8J2VeWqHuc9zJxdy1WfQJtbDxQUUy4nsqU6QPGso3HYXlI/eozg6
                bGhkJNtDVV4AAPQVv01aoFMt3T6MKLzAkjfse7zKQmQ399vQaE7lbLAV9M4FSV9s
                wksSvT7cOW9ddcdKdyV3NTbptW5PeUE8Zk/aCFLPLqOg800CAwEAATANBgkqhkiG
                9w0BAQsFAAOBgQCKMIRiThp2O+wg7M8wcNSdPzAZ61UMeisQKS5OEY90OsekWYUT
                zMkUznRtycTdTBxEqKQoJKeAXq16SezJaZYE48FpoObQc2ZLMvje7F82tOwC2kob
                v83LejX3zZnirv2PZVcFgvUE0k3a8/14enHi7j6jZu+Pl5ZM9BZ+vkBO8g==
                -----END CERTIFICATE-----"""),),
          creationTimestamp='2017-12-18T11:11:11.000-07:00',
          expireTime='2018-12-18T11:11:11.000-07:00',
          description='Self-managed certificate.',
          selfLink=prefix + 'global/sslCertificates/ssl-cert-1',
      ),
      msgs.SslCertificate(
          name='ssl-cert-2',
          region='us-west-1',
          certificate=(textwrap.dedent("""\
            -----BEGIN CERTIFICATE-----
            MIICZzCCAdACCQChX1chr91razANBgkqhkiG9w0BAQsFADB4MQswCQYDVQQGEwJV
            UzETMBEGA1UECAwKV2FzaGluZ3RvbjEQMA4GA1UEBwwHU2VhdHRsZTEPMA0GA1UE
            CgwGR29vZ2xlMRgwFgYDVQQLDA9DbG91ZCBQbGF0Zm9ybXMxFzAVBgNVBAMMDmdj
            bG91ZCBjb21wdXRlMB4XDTE0MTAxMzIwMzExNVoXDTE1MTAxMzIwMzExNVoweDEL
            MAkGA1UEBhMCVVMxEzARBgNVBAgMCldhc2hpbmd0b24xEDAOBgNVBAcMB1NlYXR0
            bGUxDzANBgNVBAoMBkdvb2dsZTEYMBYGA1UECwwPQ2xvdWQgUGxhdGZvcm1zMRcw
            FQYDVQQDDA5nY2xvdWQgY29tcHV0ZTCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkC
            gYEAq3S7ZDKHHwdro6f9Zxk8kNZ39a2ejqls4LMropt+RpkHqpaQK17Q2rUykw+f
            P+mXojUB1ZUKkrCE+xcEHeafUgG1lBof56v2bSzIQVeeS1chvDNYGqweEHIkbFHv
            8e8RY9XPkk4hMcW+uxrzaKv1yddBucyETLa3/dYmaEzHcOsCAwEAATANBgkqhkiG
            9w0BAQsFAAOBgQAxBD6GUsgGYfeHkjo3CK/X5cbaPTdUncD13uaI4Q31GWZGhGJX
            t9hMvJdXQ6vzKXBuX6ZLUxvL9SFT+pMLTWGStUFNcDFv/Fqdcre0jPoYEJv/tOHT
            n82GtW9nMhZfVj2PrRiuZwOV8qB6+uEadbcPcET3TcH1WJacbBlHufk1wQ==
            -----END CERTIFICATE-----""")),
          creationTimestamp='2014-10-04T07:56:33.679-07:00',
          description='Self-managed certificate two.',
          selfLink=prefix + 'regions/us-west-1/sslCertificates/ssl-cert-2',
      ),
      msgs.SslCertificate(
          name='ssl-cert-3',
          type=msgs.SslCertificate.TypeValueValuesEnum.MANAGED,
          managed=msgs.SslCertificateManagedSslCertificate(
              domains=[
                  'test1.certsbridge.com',
                  # Punycode for Ṳᾔḯ¢◎ⅾℯ.certsbridge.com
                  'xn--8a342mzfam5b18csni3w.certsbridge.com',
              ],
              status=msgs.SslCertificateManagedSslCertificate
              .StatusValueValuesEnum.ACTIVE,
              domainStatus=msgs.SslCertificateManagedSslCertificate
              .DomainStatusValue(additionalProperties=[
                  msgs.SslCertificateManagedSslCertificate.DomainStatusValue
                  .AdditionalProperty(
                      key='test1.certsbridge.com',
                      value=msgs.SslCertificateManagedSslCertificate
                      .DomainStatusValue.AdditionalProperty.ValueValueValuesEnum
                      .ACTIVE,
                  ),
                  msgs.SslCertificateManagedSslCertificate.DomainStatusValue
                  .AdditionalProperty(
                      key='xn--8a342mzfam5b18csni3w.certsbridge.com',
                      value=msgs.SslCertificateManagedSslCertificate
                      .DomainStatusValue.AdditionalProperty.ValueValueValuesEnum
                      .FAILED_CAA_FORBIDDEN,
                  ),
              ])),
          creationTimestamp='2017-12-17T10:00:00.000-07:00',
          expireTime='2018-12-17T10:00:00.000-07:00',
          description='Managed certificate.',
          selfLink=prefix + 'global/sslCertificates/ssl-cert-3',
      ),
  ]


def MakeOrgSecurityPolicy(msgs, security_policy_ref):
  return msgs.SecurityPolicy(
      name=security_policy_ref.Name(),
      description='test-description',
      displayName='display-name',
      id=123,
      fingerprint=b'=g\313\0305\220\f\266',
      selfLink=security_policy_ref.SelfLink())


def MakeSslPolicies(msgs, api):
  """Make ssl policy test resources for the given api version."""
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.SslPolicy(
          name='ssl-policy-1',
          profile=msgs.SslPolicy.ProfileValueValuesEnum('COMPATIBLE'),
          minTlsVersion=msgs.SslPolicy.MinTlsVersionValueValuesEnum('TLS_1_0'),
          customFeatures=[],
          selfLink=(prefix +
                    '/projects/my-project/global/sslPolicies/ssl-policy-1'))
  ]


SSL_POLICIES_ALPHA = MakeSslPolicies(alpha_messages, 'alpha')


def MakeVpnTunnels(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  region1 = prefix + '/projects/my-project/regions/region-1'
  region2 = prefix + '/projects/my-project/regions/region-2'
  return [
      msgs.VpnTunnel(
          creationTimestamp='2011-11-11T17:54:10.636-07:00',
          description='the first tunnel',
          ikeVersion=1,
          name='tunnel-1',
          peerIp='1.1.1.1',
          region=region1,
          selfLink=region1 + '/vpnTunnels/tunnel-1',
          sharedSecretHash='ff33f3a693905de7e85178529e3a13feb85a3964',
          status=msgs.VpnTunnel.StatusValueValuesEnum.ESTABLISHED,
          targetVpnGateway=region1 + '/targetVpnGateways/gateway-1'
      ),
      msgs.VpnTunnel(
          creationTimestamp='2022-22-22T17:54:10.636-07:00',
          description='the second tunnel',
          ikeVersion=2,
          name='tunnel-2',
          peerIp='2.2.2.2',
          region=region2,
          selfLink=region2 + '/vpnTunnels/tunnel-2',
          sharedSecretHash='2f23232623202de7e85178529e3a13feb85a3964',
          status=msgs.VpnTunnel.StatusValueValuesEnum.ESTABLISHED,
          targetVpnGateway=region2 + '/targetVpnGateways/gateway-2'
      ),
      msgs.VpnTunnel(
          creationTimestamp='2033-33-33T17:54:10.636-07:00',
          description='the third tunnel',
          ikeVersion=2,
          name='tunnel-3',
          peerIp='3.3.3.3',
          region=region1,
          selfLink=region1 + '/vpnTunnels/tunnel-3',
          sharedSecretHash='3f33333633303de7e85178539e3a13feb85a3964',
          status=msgs.VpnTunnel.StatusValueValuesEnum.ESTABLISHED,
          targetVpnGateway=region1 + '/targetVpnGateways/gateway-3'
      )
  ]


VPN_TUNNELS_BETA = MakeVpnTunnels(beta_messages, 'beta')
VPN_TUNNELS_V1 = MakeVpnTunnels(beta_messages, 'v1')


ZONES = [
    messages.Zone(
        name='us-central1-a',
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/us-central1'),
        status=messages.Zone.StatusValueValuesEnum.UP,
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/us-central1-a'),
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.DEPRECATED,
            deleted='2015-03-29T00:00:00.000-07:00',
            replacement=('https://compute.googleapis.com/compute/v1/projects/'
                         'my-project/zones/us-central1-b'))),

    messages.Zone(
        name='us-central1-b',
        status=messages.Zone.StatusValueValuesEnum.UP,
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/us-central1'),
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/us-central1-b')),

    messages.Zone(
        name='europe-west1-a',
        status=messages.Zone.StatusValueValuesEnum.UP,
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/europe-west1'),
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/europe-west1-a')),

    messages.Zone(
        name='europe-west1-b',
        status=messages.Zone.StatusValueValuesEnum.DOWN,
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/europe-west1'),
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/europe-west1-a'),
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.DELETED,
            deleted='2015-03-29T00:00:00.000-07:00',
            replacement=('https://compute.googleapis.com/compute/v1/projects/'
                         'my-project/zones/europe-west1-a'))),
]

BETA_ZONES = [
    beta_messages.Zone(
        name='us-central1-a',
        region=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'regions/us-central1'),
        status=beta_messages.Zone.StatusValueValuesEnum.UP,
        selfLink=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'zones/us-central1-a')),
    beta_messages.Zone(
        name='us-central1-b',
        status=beta_messages.Zone.StatusValueValuesEnum.UP,
        region=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'regions/us-central1'),
        selfLink=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'zones/us-central1-b')),
    beta_messages.Zone(
        name='europe-west1-a',
        status=beta_messages.Zone.StatusValueValuesEnum.UP,
        region=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'regions/europe-west1'),
        selfLink=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'zones/europe-west1-a')),
    beta_messages.Zone(
        name='europe-west1-b',
        status=beta_messages.Zone.StatusValueValuesEnum.DOWN,
        region=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'regions/europe-west1'),
        selfLink=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'zones/europe-west1-b')),
]

BETA_SUBNETWORKS = [
    beta_messages.Subnetwork(
        name='my-subnet1',
        network=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'global/networks/my-network'),
        ipCidrRange='10.0.0.0/24',
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/us-central1'),
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'regions/us-central1/subnetworks/my-subnet1'),
    ),
    beta_messages.Subnetwork(
        name='my-subnet2',
        network=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'global/networks/my-other-network'),
        ipCidrRange='10.0.0.0/24',
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/us-central1'),
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'regions/us-central1/subnetworks/my-subnet2'),
    ),
]


def MakePublicAdvertisedPrefixes(msgs, api):
  """Creates a set of public advertised prefixes messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.

  Returns:
    A list of message objects representing public advertised prefixes.
  """
  prefix = _COMPUTE_PATH + '/' + api
  status_enum = msgs.PublicAdvertisedPrefix.StatusValueValuesEnum
  return [
      msgs.PublicAdvertisedPrefix(
          description='My PAP 1',
          kind='compute#publicAdvertisedPrefix',
          name='my-pap1',
          selfLink=(prefix + '/projects/my-project/'
                    'publicAdvertisedPrefixes/my-pap1'),
          ipCidrRange='1.2.3.0/24',
          dnsVerificationIp='1.2.3.4',
          sharedSecret='vader is luke\'s father',
          status=status_enum.VALIDATED),
      msgs.PublicAdvertisedPrefix(
          description='My PAP number two',
          kind='compute#publicAdvertisedPrefix',
          name='my-pap2',
          selfLink=(prefix + '/projects/my-project/'
                    'publicAdvertisedPrefixes/my-pap2'),
          ipCidrRange='100.66.0.0/16',
          dnsVerificationIp='100.66.20.1',
          sharedSecret='longsecretisbestsecret',
          status=status_enum.PTR_CONFIGURED),
  ]


PUBLIC_ADVERTISED_PREFIXES_ALPHA = MakePublicAdvertisedPrefixes(
    alpha_messages, 'alpha')


def MakePublicDelegatedPrefixes(msgs, api):
  """Creates a set of public delegated prefixes messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.

  Returns:
    A list of message objects representing public delegated prefixes.
  """
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.PublicDelegatedPrefix(
          description='My global PDP 1',
          fingerprint=b'1234',
          ipCidrRange='1.2.3.128/25',
          kind='compute#globalPublicDelegatedPrefix',
          name='my-pdp1',
          selfLink=(prefix + '/projects/my-project/global/'
                    'publicDelegatedPrefixes/my-pdp1'),
          parentPrefix=(prefix + '/projects/my-project/global/'
                        'publicAdvertisedPrefixes/my-pap1')
      ),
      msgs.PublicDelegatedPrefix(
          description='My PDP 2',
          fingerprint=b'12345',
          ipCidrRange='1.2.3.12/30',
          kind='compute#publicDelegatedPrefix',
          name='my-pdp2',
          selfLink=(prefix + '/projects/my-project/regions/us-central1/'
                             'publicDelegatedPrefixes/my-pdp2'),
          parentPrefix=(prefix + '/projects/my-project/global/'
                                 'publicAdvertisedPrefixes/my-pap1')
      ),
      msgs.PublicDelegatedPrefix(
          description='My PDP 3',
          fingerprint=b'123456',
          ipCidrRange='1.2.3.40/30',
          kind='compute#publicDelegatedPrefix',
          name='my-pdp3',
          selfLink=(prefix + '/projects/my-project/regions/us-east1/'
                             'publicDelegatedPrefixes/my-pdp3'),
          parentPrefix=(prefix + '/projects/my-project/global/'
                                 'publicAdvertisedPrefixes/my-pap1')
      )
  ]


PUBLIC_DELEGATED_PREFIXES_ALPHA = MakePublicDelegatedPrefixes(
    alpha_messages, 'alpha')
