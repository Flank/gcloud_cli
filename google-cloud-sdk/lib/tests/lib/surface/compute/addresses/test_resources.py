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

ADDRESSES = [
    messages.Address(
        address='23.251.134.124',
        name='address-1',
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/region-1'),
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'regions/region-1/addresses/address-1'),
        status=messages.Address.StatusValueValuesEnum.IN_USE),
    messages.Address(
        address='23.251.134.125',
        name='address-2',
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/region-1'),
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'regions/region-1/addresses/address-2'),
        status=messages.Address.StatusValueValuesEnum.RESERVED),
]

GLOBAL_ADDRESSES = [
    messages.Address(
        address='23.251.134.126',
        name='global-address-1',
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'global/addresses/global-address-1'),
        status=messages.Address.StatusValueValuesEnum.IN_USE),
    messages.Address(
        address='23.251.134.127',
        name='global-address-2',
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'global/addresses/global-address-2'),
        status=messages.Address.StatusValueValuesEnum.RESERVED),
]
