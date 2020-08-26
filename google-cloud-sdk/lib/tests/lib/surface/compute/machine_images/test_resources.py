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

_COMPUTE_PATH = 'https://compute.googleapis.com/compute'


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
                      mode=(msgs.SavedAttachedDisk.ModeValueValuesEnum
                            .READ_WRITE),
                      source='disk-1',
                      type=(msgs.SavedAttachedDisk.TypeValueValuesEnum
                            .PERSISTENT),
                  ),
                  msgs.SavedAttachedDisk(
                      autoDelete=True,
                      boot=True,
                      deviceName='device-2',
                      mode=(
                          msgs.SavedAttachedDisk.ModeValueValuesEnum.READ_ONLY),
                      type=(msgs.SavedAttachedDisk.TypeValueValuesEnum.SCRATCH),
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
