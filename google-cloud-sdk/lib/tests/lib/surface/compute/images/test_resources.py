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

IMAGES = [
    messages.Image(
        name='image-1',
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'global/images/image-1'),
        status=messages.Image.StatusValueValuesEnum.READY),
    messages.Image(
        name='image-2',
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'global/images/image-2'),
        status=messages.Image.StatusValueValuesEnum.READY),
    messages.Image(
        name='image-3',
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.DEPRECATED),
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'global/images/image-3'),
        status=messages.Image.StatusValueValuesEnum.READY),
    messages.Image(
        name='image-4',
        deprecated=messages.DeprecationStatus(deprecated='2019-04-01T15:00:00'),
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'global/images/image-4'),
        status=messages.Image.StatusValueValuesEnum.READY),
]

CENTOS_IMAGES = [
    messages.Image(
        name='centos-6-v20140408',
        family='centos-6',
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/centos-cloud/'
            'global/images/centos-6-v20140408'),
        status=messages.Image.StatusValueValuesEnum.READY),
    messages.Image(
        name='centos-6-v20140318',
        family='centos-6',
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.DEPRECATED),
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/centos-cloud/'
            'global/images/centos-6-v20140318'),
        status=messages.Image.StatusValueValuesEnum.READY),
]
