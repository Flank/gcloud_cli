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
"""Resources that are shared by two or more network endpoint group tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis

alpha_messages = core_apis.GetMessagesModule('compute', 'alpha')
beta_messages = core_apis.GetMessagesModule('compute', 'beta')
messages = core_apis.GetMessagesModule('compute', 'v1')

_COMPUTE_PATH = 'https://compute.googleapis.com/compute'

_V1_URI_PREFIX = _COMPUTE_PATH + '/v1/projects/my-project/'
_ALPHA_URI_PREFIX = _COMPUTE_PATH + '/alpha/projects/my-project/'
_BETA_URI_PREFIX = _COMPUTE_PATH + '/beta/projects/my-project/'


def MakeNetworkEndpointGroups(msgs, api):
  """Creates a set of NEG messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.

  Returns:
    A list of message objects representing network endpoint groups.
  """
  prefix = '{}/{}'.format(_COMPUTE_PATH, api)
  neg_type_enum = msgs.NetworkEndpointGroup.NetworkEndpointTypeValueValuesEnum
  return [
      msgs.NetworkEndpointGroup(
          description='My NEG 1',
          kind='compute#networkEndpointGroup',
          network=('https://compute.googleapis.com/compute/v1/projects/'
                   'my-project/global/networks/network-1'),
          zone='zone-1',
          name='my-neg1',
          networkEndpointType=neg_type_enum.GCE_VM_IP_PORT,
          selfLink=(prefix + '/projects/my-project/zones/zone-1/'
                    'networkEndpointGroups/my-neg1'),
          size=5),
      msgs.NetworkEndpointGroup(
          description='My NEG Too',
          kind='compute#networkEndpointGroup',
          network=('https://compute.googleapis.com/compute/v1/projects/'
                   'my-project/global/networks/network-2'),
          zone='zone-2',
          name='my-neg2',
          networkEndpointType=neg_type_enum.GCE_VM_IP_PORT,
          selfLink=(prefix + '/projects/my-project/zones/zone-2/'
                    'networkEndpointGroups/my-neg2'),
          size=2),
      msgs.NetworkEndpointGroup(
          description='My NEG 1',
          kind='compute#networkEndpointGroup',
          network=('https://www.googleapis.com/compute/v1/projects/'
                   'my-project/global/networks/network-1'),
          zone='zone-1',
          name='my-neg3',
          networkEndpointType=neg_type_enum.GCE_VM_IP_PORT,
          selfLink=(prefix + '/projects/my-project/zones/zone-1/'
                    'networkEndpointGroups/my-neg3'),
          size=3),
  ]


def MakeGlobalNetworkEndpointGroups(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  neg_type_enum = msgs.NetworkEndpointGroup.NetworkEndpointTypeValueValuesEnum
  return [
      msgs.NetworkEndpointGroup(
          description='My Global NEG',
          kind='compute#networkEndpointGroup',
          name='my-global-neg',
          networkEndpointType=neg_type_enum.INTERNET_IP_PORT,
          selfLink=(prefix + '/projects/my-project/global/'
                    'networkEndpointGroups/my-global-neg'),
          size=1),
      msgs.NetworkEndpointGroup(
          description='My Global NEG FQDN',
          kind='compute#networkEndpointGroup',
          name='my-global-neg-fqdn',
          networkEndpointType=neg_type_enum.INTERNET_FQDN_PORT,
          selfLink=(prefix + '/projects/my-project/global/'
                    'networkEndpointGroups/my-global-neg-fqdn'),
          size=2),
  ]


def MakeRegionNetworkEndpointGroups(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  neg_type_enum = msgs.NetworkEndpointGroup.NetworkEndpointTypeValueValuesEnum
  return [
      msgs.NetworkEndpointGroup(
          description='My Cloud Run Serverless NEG',
          kind='compute#networkEndpointGroup',
          region='region-1',
          name='my-cloud-run-neg',
          networkEndpointType=neg_type_enum.SERVERLESS,
          selfLink=(prefix + '/projects/my-project/regions/region-1/'
                    'networkEndpointGroups/my-cloud-run-neg'),
          cloudRun=msgs.NetworkEndpointGroupCloudRun(
              service='cloud-run-service', tag='cloud-run-tag'),
          size=0),
      msgs.NetworkEndpointGroup(
          description='My App Engine Serverless NEG',
          kind='compute#networkEndpointGroup',
          region='region-2',
          name='my-app-engine-neg',
          networkEndpointType=neg_type_enum.SERVERLESS,
          selfLink=(prefix + '/projects/my-project/regions/region-2/'
                    'networkEndpointGroups/my-app-engine-neg'),
          appEngine=msgs.NetworkEndpointGroupAppEngine(),
          size=0),
      msgs.NetworkEndpointGroup(
          description='My Cloud Function Serverless NEG',
          kind='compute#networkEndpointGroup',
          region='region-3',
          name='my-cloud-function-neg',
          networkEndpointType=neg_type_enum.SERVERLESS,
          selfLink=(prefix + '/projects/my-project/regions/region-3/'
                    'networkEndpointGroups/my-cloud-function-neg'),
          cloudFunction=msgs.NetworkEndpointGroupCloudFunction(
              urlMask='/<function>'),
          size=0)
  ]


NETWORK_ENDPOINT_GROUPS = MakeNetworkEndpointGroups(messages, 'v1')
NETWORK_ENDPOINT_GROUPS_ALPHA = MakeNetworkEndpointGroups(
    alpha_messages, 'alpha')
NETWORK_ENDPOINT_GROUPS_BETA = MakeNetworkEndpointGroups(beta_messages, 'beta')
GLOBAL_NETWORK_ENDPOINT_GROUPS = MakeGlobalNetworkEndpointGroups(messages, 'v1')
GLOBAL_NETWORK_ENDPOINT_GROUPS_ALPHA = MakeGlobalNetworkEndpointGroups(
    alpha_messages, 'alpha')
GLOBAL_NETWORK_ENDPOINT_GROUPS_BETA = MakeGlobalNetworkEndpointGroups(
    beta_messages, 'beta')
REGION_NETWORK_ENDPOINT_GROUPS_ALPHA = MakeRegionNetworkEndpointGroups(
    alpha_messages, 'alpha')
REGION_NETWORK_ENDPOINT_GROUPS_BETA = MakeRegionNetworkEndpointGroups(
    beta_messages, 'beta')
