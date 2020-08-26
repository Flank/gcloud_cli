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

DISKS = [
    messages.Disk(
        name='disk-1',
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-1/disks/disk-1'),
        sizeGb=10,
        status=messages.Disk.StatusValueValuesEnum.READY,
        type=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1/diskTypes/pd-ssd'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),
    messages.Disk(
        name='disk-2',
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-1/disks/disk-2'),
        sizeGb=10,
        status=messages.Disk.StatusValueValuesEnum.READY,
        type=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1/diskTypes/pd-ssd'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),
    messages.Disk(
        name='disk-3',
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-1/disks/disk-3'),
        sizeGb=10,
        status=messages.Disk.StatusValueValuesEnum.READY,
        type=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1/diskTypes/pd-standard'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),
]
