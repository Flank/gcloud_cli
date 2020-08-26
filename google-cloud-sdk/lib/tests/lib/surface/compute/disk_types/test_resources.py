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


def MakeDiskTypes(msgs,
                  api,
                  scope_type='zone',
                  scope_name='zone-1',
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
          selfLink=('{0}/projects/{1}/{2}/{3}/diskTypes/pd-standard'.format(
              prefix, project, scope_type + 's', scope_name)),
      ),
      msgs.DiskType(
          deprecated=msgs.DeprecationStatus(
              state=msgs.DeprecationStatus.StateValueValuesEnum.OBSOLETE),
          name='pd-ssd',
          validDiskSize='10GB-1TB',
          selfLink=('{0}/projects/{1}/{2}/{3}/diskTypes/pd-ssd'.format(
              prefix, project, scope_type + 's', scope_name))),
  ]
  for disk_type in disk_types:
    # Field 'region' is missing in regional disk types.
    if scope_type == 'zone':
      setattr(
          disk_type, scope_type,
          '{0}/projects/{1}/{2}/{3}'.format(prefix, project, scope_type + 's',
                                            scope_name))
  return disk_types


DISK_TYPES = [
    messages.DiskType(
        name='pd-standard',
        validDiskSize='10GB-10TB',
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-1/diskTypes/pd-standard'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),
    messages.DiskType(
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.OBSOLETE),
        name='pd-ssd',
        validDiskSize='10GB-1TB',
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-1/diskTypes/pd-ssd'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),
]
