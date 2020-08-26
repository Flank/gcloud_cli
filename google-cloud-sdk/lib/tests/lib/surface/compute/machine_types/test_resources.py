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

MACHINE_TYPES = [
    messages.MachineType(
        name='n1-standard-1',
        guestCpus=1,
        memoryMb=3840,
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-1/machineTypes/n1-standard-1'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),
    messages.MachineType(
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.OBSOLETE),
        name='n1-standard-1-d',
        guestCpus=1,
        memoryMb=3840,
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-1/machineTypes/n1-standard-1-d'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),
    messages.MachineType(
        name='n1-highmem-2',
        guestCpus=2,
        memoryMb=30720,
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-1/machineTypes/n1-standard-2'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),
]
