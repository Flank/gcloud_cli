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

alpha_messages = core_apis.GetMessagesModule('compute', 'alpha')
beta_messages = core_apis.GetMessagesModule('compute', 'beta')
messages = core_apis.GetMessagesModule('compute', 'v1')

_COMPUTE_PATH = 'https://compute.googleapis.com/compute'

_V1_URI_PREFIX = _COMPUTE_PATH + '/v1/projects/my-project/'
_ALPHA_URI_PREFIX = _COMPUTE_PATH + '/alpha/projects/my-project/'
_BETA_URI_PREFIX = _COMPUTE_PATH + '/beta/projects/my-project/'


def _GetMessagesForApi(api):
  if api == 'alpha':
    return alpha_messages
  elif api == 'beta':
    return beta_messages
  elif api == 'v1':
    return messages
  else:
    assert False


def MakeInstances(msgs, api):
  """Creates a set of VM instance messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.

  Returns:
    A list of message objects representing VM instances.
  """
  prefix = _COMPUTE_PATH + '/' + api
  # Create a Scheduling message that includes the preemptible flag, now that all
  # API versions support it.
  scheduling = msgs.Scheduling(
      automaticRestart=False,
      onHostMaintenance=msgs.Scheduling.
      OnHostMaintenanceValueValuesEnum.TERMINATE,
      preemptible=False)
  return [
      msgs.Instance(
          machineType=(
              prefix + '/projects/my-project/zones/zone-1/'
              'machineTypes/n1-standard-1'),
          name='instance-1',
          networkInterfaces=[
              msgs.NetworkInterface(
                  networkIP='10.0.0.1',
                  accessConfigs=[
                      msgs.AccessConfig(natIP='23.251.133.75'),
                  ],
              ),
          ],
          scheduling=scheduling,
          status=msgs.Instance.StatusValueValuesEnum.RUNNING,
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/instances/instance-1'),
          zone=(prefix + '/projects/my-project/zones/zone-1')),

      msgs.Instance(
          machineType=(
              prefix + '/projects/my-project/'
              'zones/zone-1/machineTypes/n1-standard-1'),
          name='instance-2',
          networkInterfaces=[
              msgs.NetworkInterface(
                  networkIP='10.0.0.2',
                  accessConfigs=[
                      msgs.AccessConfig(natIP='23.251.133.74'),
                  ],
              ),
          ],
          scheduling=scheduling,
          status=msgs.Instance.StatusValueValuesEnum.RUNNING,
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/instances/instance-2'),
          zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'zones/zone-1')),

      msgs.Instance(
          machineType=(
              prefix + '/projects/my-project/'
              'zones/zone-1/machineTypes/n1-standard-2'),
          name='instance-3',
          networkInterfaces=[
              msgs.NetworkInterface(
                  networkIP='10.0.0.3',
                  accessConfigs=[
                      msgs.AccessConfig(natIP='23.251.133.76'),
                  ],
              ),
          ],
          scheduling=scheduling,
          status=msgs.Instance.StatusValueValuesEnum.RUNNING,
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/instances/instance-3'),
          zone=(prefix + '/projects/my-project/zones/zone-1')),
  ]

INSTANCES_ALPHA = MakeInstances(alpha_messages, 'alpha')
INSTANCES_BETA = MakeInstances(beta_messages, 'beta')
INSTANCES_V1 = MakeInstances(messages, 'v1')

