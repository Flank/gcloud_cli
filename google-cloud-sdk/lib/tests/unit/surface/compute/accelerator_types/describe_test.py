# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for the accelerator types describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base

# pylint: disable=line-too-long
EXPECED_OUTPUT = """\
    description: Nvidia Tesla K80
    name: nvidia-tesla-k80
    selfLink: https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-1/accelerator-types/nvidia-tesla-k80
    zone: https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-1
    description: Nvidia Grid K2
    name: nvidia-grid-k2
    selfLink: https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-2/accelerator-types/nvidia-grid-k2
    zone: https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-2
    description: Nvidia Grid K2
    name: nvidia-grid-k2
    selfLink: https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-1/accelerator-types/nvidia-grid-k2
    zone: https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-1
    """
# pylint: enable=line-too-long


class AcceleratorTypesDescribeTest(test_base.BaseTest):

  def _MakeAcceleratorTypes(self, msgs, api):
    """Creates a set of accelerator types messages for the given API version.

    Args:
      msgs: The compute messages API handle.
      api: The API version for which to create the instances.

    Returns:
      A list of message objects representing accelerator types.
    """
    prefix = 'https://compute.googleapis.com/compute/' + api
    return [
        msgs.AcceleratorType(
            name='nvidia-tesla-k80',
            description='Nvidia Tesla K80',
            selfLink=(prefix + '/projects/my-project/'
                      'zones/zone-1/accelerator-types/nvidia-tesla-k80'),
            zone=(prefix + '/projects/my-project/zones/zone-1')),
        msgs.AcceleratorType(
            name='nvidia-grid-k2',
            description='Nvidia Grid K2',
            selfLink=(prefix + '/projects/my-project/'
                      'zones/zone-1/accelerator-types/nvidia-grid-k2'),
            zone=(prefix + '/projects/my-project/zones/zone-1')),
        msgs.AcceleratorType(
            name='nvidia-grid-k2',
            description='Nvidia Grid K2',
            selfLink=(prefix + '/projects/my-project/'
                      'zones/zone-2/accelerator-types/nvidia-grid-k2'),
            zone=(prefix + '/projects/my-project/zones/zone-2')),
    ]

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')

  def testTeslaK80Case(self):
    accelerator_types = self._MakeAcceleratorTypes(self.messages, 'v1')
    self.make_requests.side_effect = iter([
        [accelerator_types[0]],
        [accelerator_types[2]],
        [accelerator_types[1]],
    ])
    self.Run("""
        compute accelerator-types describe nvidia-tesla-k80 --zone zone-1
        """)
    self.CheckRequests([(self.compute.acceleratorTypes, 'Get',
                         self.messages.ComputeAcceleratorTypesGetRequest(
                             acceleratorType='nvidia-tesla-k80',
                             project='my-project',
                             zone='zone-1'))])

    self.Run("""
        compute accelerator-types describe nvidia-grid-k2 --zone zone-2
        """)
    self.CheckRequests([(self.compute.acceleratorTypes, 'Get',
                         self.messages.ComputeAcceleratorTypesGetRequest(
                             acceleratorType='nvidia-grid-k2',
                             project='my-project',
                             zone='zone-2'))])

    self.Run("""
        compute accelerator-types describe nvidia-grid-k2 --zone zone-1
        """)
    self.CheckRequests([(self.compute.acceleratorTypes, 'Get',
                         self.messages.ComputeAcceleratorTypesGetRequest(
                             acceleratorType='nvidia-grid-k2',
                             project='my-project',
                             zone='zone-1'))])

    self.AssertOutputEquals(EXPECED_OUTPUT, normalize_space=True)


if __name__ == '__main__':
  test_case.main()
