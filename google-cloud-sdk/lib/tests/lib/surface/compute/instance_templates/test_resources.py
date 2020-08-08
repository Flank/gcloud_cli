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


def MakeInstanceTemplates(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.InstanceTemplate(
          name='instance-template-1',
          selfLink=(prefix + '/projects/my-project/'
                    'global/instanceTemplates/instance-template-1'),
          creationTimestamp='2013-09-06T17:54:10.636-07:00',
          properties=msgs.InstanceProperties(
              networkInterfaces=[
                  msgs.NetworkInterface(
                      networkIP='10.0.0.1',
                      accessConfigs=[
                          msgs.AccessConfig(natIP='23.251.133.75'),
                      ],
                  ),
              ],
              disks=[
                  msgs.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      deviceName='device-1',
                      mode=(msgs.AttachedDisk.ModeValueValuesEnum.READ_WRITE),
                      source='disk-1',
                      type=(msgs.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                  ),
              ],
              machineType='n1-standard-1',
              scheduling=msgs.Scheduling(
                  automaticRestart=False,
                  onHostMaintenance=msgs.Scheduling
                  .OnHostMaintenanceValueValuesEnum.TERMINATE,
                  preemptible=False,
              ),
          )),
      msgs.InstanceTemplate(
          name='instance-template-2',
          selfLink=(prefix + '/projects/my-project/'
                    'global/instanceTemplates/instance-template-2'),
          creationTimestamp='2013-10-06T17:54:10.636-07:00',
          properties=msgs.InstanceProperties(
              networkInterfaces=[
                  msgs.NetworkInterface(
                      networkIP='10.0.0.2',
                      accessConfigs=[
                          msgs.AccessConfig(natIP='23.251.133.76'),
                      ],
                  ),
              ],
              machineType='n1-highmem-1',
              scheduling=msgs.Scheduling(
                  automaticRestart=False,
                  onHostMaintenance=msgs.Scheduling
                  .OnHostMaintenanceValueValuesEnum.TERMINATE,
                  preemptible=False,
              ),
          )),
      msgs.InstanceTemplate(
          name='instance-template-3',
          selfLink=(prefix + '/projects/my-project/'
                    'global/instanceTemplates/instance-template-3'),
          creationTimestamp='2013-11-06T17:54:10.636-07:00',
          properties=msgs.InstanceProperties(
              networkInterfaces=[
                  msgs.NetworkInterface(
                      networkIP='10.0.0.3',
                      accessConfigs=[
                          msgs.AccessConfig(natIP='23.251.133.77'),
                      ],
                  ),
              ],
              machineType='n2-custom-6-17152',
              scheduling=msgs.Scheduling(
                  automaticRestart=False,
                  onHostMaintenance=msgs.Scheduling
                  .OnHostMaintenanceValueValuesEnum.TERMINATE,
                  preemptible=False,
              ),
          ))
  ]


INSTANCE_TEMPLATES_V1 = MakeInstanceTemplates(messages, 'v1')
INSTANCE_TEMPLATES_BETA = MakeInstanceTemplates(beta_messages, 'beta')
INSTANCE_TEMPLATES_ALPHA = MakeInstanceTemplates(alpha_messages, 'alpha')
