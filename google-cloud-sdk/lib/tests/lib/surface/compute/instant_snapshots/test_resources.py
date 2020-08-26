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


def MakeInstantSnapshots(msgs, api):
  """Creates a set of instant snapshots messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.

  Returns:
    A list of message objects representing instant snapshots.
  """
  prefix = _COMPUTE_PATH + '/' + api + '/projects/my-project'
  zone_scope = prefix + '/zones/zone-1'
  region_scope = prefix + '/regions/region-1'

  return [
      msgs.InstantSnapshot(
          diskSizeGb=10,
          name='ips-1',
          selfLink=(zone_scope + '/instantsnapshots/ips-1'),
          sourceDisk=(zone_scope + '/disks/disk-1'),
          status=msgs.InstantSnapshot.StatusValueValuesEnum.READY,
          zone=zone_scope),
      msgs.InstantSnapshot(
          diskSizeGb=10,
          name='ips-2',
          selfLink=(zone_scope + '/instantsnapshots/ips-2'),
          sourceDisk=(zone_scope + '/disks/disk-2'),
          status=msgs.InstantSnapshot.StatusValueValuesEnum.READY,
          zone=zone_scope),
      msgs.InstantSnapshot(
          diskSizeGb=10,
          name='ips-3',
          selfLink=(region_scope + '/instantsnapshots/ips-3'),
          sourceDisk=(region_scope + '/disks/disk-3'),
          status=msgs.InstantSnapshot.StatusValueValuesEnum.READY,
          region=region_scope),
      msgs.InstantSnapshot(
          diskSizeGb=10,
          name='ips-4',
          selfLink=(region_scope + '/instantsnapshots/ips-4'),
          sourceDisk=(region_scope + '/disks/disk-4'),
          status=msgs.InstantSnapshot.StatusValueValuesEnum.READY,
          region=region_scope),
  ]


INSTANT_SNAPSHOT_ALPHA = MakeInstantSnapshots(alpha_messages, 'alpha')
