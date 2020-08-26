# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

from googlecloudsdk.api_lib.util import apis as core_apis

messages = core_apis.GetMessagesModule('compute', 'v1')

_COMPUTE_PATH = 'https://compute.googleapis.com/compute'


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
          nodeAffinityLabels=node_affinity_value(additionalProperties=[
              node_affinity_value.AdditionalProperty(
                  key='environment', value='prod'),
              node_affinity_value.AdditionalProperty(
                  key='nodeGrouping', value='frontend')
          ]),
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
          nodeAffinityLabels=node_affinity_value(additionalProperties=[
              node_affinity_value.AdditionalProperty(
                  key='environment', value='prod'),
              node_affinity_value.AdditionalProperty(
                  key='nodeGrouping', value='backend')
          ]),
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
