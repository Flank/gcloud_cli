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

GLOBAL_OPERATIONS = [
    messages.Operation(
        name='operation-1',
        status=messages.Operation.StatusValueValuesEnum.DONE,
        operationType='insert',
        insertTime='2014-09-04T09:55:33.679-07:00',
        selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                  'my-project/global/operations/operation-1'),
        targetLink=('https://compute.googleapis.com/compute/v1/projects/'
                    'my-project/resource/resource-1')),
]

ALPHA_GLOBAL_OPERATIONS = [
    alpha_messages.Operation(
        name='operation-1',
        status=alpha_messages.Operation.StatusValueValuesEnum.DONE,
        operationType='insert',
        insertTime='2014-09-04T09:55:33.679-07:00',
        selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                  'my-project/global/operations/operation-1'),
        targetLink=('https://compute.googleapis.com/compute/v1/projects/'
                    'my-project/resource/resource-1')),
]

BETA_GLOBAL_OPERATIONS = [
    beta_messages.Operation(
        name='operation-1',
        status=beta_messages.Operation.StatusValueValuesEnum.DONE,
        operationType='insert',
        insertTime='2014-09-04T09:55:33.679-07:00',
        selfLink=('https://compute.googleapis.com/compute/beta/projects/'
                  'my-project/global/operations/operation-1'),
        targetLink=('https://compute.googleapis.com/compute/beta/projects/'
                    'my-project/resource/resource-1')),
]


REGIONAL_OPERATIONS = [
    messages.Operation(
        name='operation-2',
        operationType='insert',
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/region-1'),
        status=messages.Operation.StatusValueValuesEnum.DONE,
        insertTime='2014-09-04T09:53:33.679-07:00',
        selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                  'my-project/regions/region-1/operations/operation-2'),
        targetLink=('https://compute.googleapis.com/compute/v1/projects/'
                    'my-project/regions/region-1/resource/resource-2')),
]

BETA_REGIONAL_OPERATIONS = [
    beta_messages.Operation(
        name='operation-2', operationType='insert',
        region=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'regions/region-1'),
        status=beta_messages.Operation.StatusValueValuesEnum.DONE,
        insertTime='2014-09-04T09:53:33.679-07:00',
        selfLink=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'regions/region-1/operations/operation-2'),
        targetLink=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'regions/region-1/resource/resource-2'))]


ZONAL_OPERATIONS = [
    messages.Operation(
        name='operation-3',
        httpErrorStatusCode=409,
        operationType='insert',
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1'),
        status=messages.Operation.StatusValueValuesEnum.DONE,
        insertTime='2014-09-04T09:56:33.679-07:00',
        selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                  'my-project/zones/zone-1/operations/operation-3'),
        targetLink=('https://compute.googleapis.com/compute/v1/projects/'
                    'my-project/zones/zone-1/resource/resource-3')),
]

BETA_ZONAL_OPERATIONS = [
    beta_messages.Operation(
        name='operation-3',
        httpErrorStatusCode=409,
        operationType='insert',
        zone=('https://compute.googleapis.com/compute/beta/projects/my-project/'
              'zones/zone-1'),
        status=beta_messages.Operation.StatusValueValuesEnum.DONE,
        insertTime='2014-09-04T09:56:33.679-07:00',
        selfLink=('https://compute.googleapis.com/compute/beta/projects/'
                  'my-project/zones/zone-1/operations/operation-3'),
        targetLink=('https://compute.googleapis.com/compute/beta/projects/'
                    'my-project/zones/zone-1/resource/resource-3')),
]
