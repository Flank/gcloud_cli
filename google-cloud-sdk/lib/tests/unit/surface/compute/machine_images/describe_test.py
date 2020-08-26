# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for the machine-images describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.machine_images import test_resources


class MachineImagesDescribeTestBeta(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)
    self.api_version = 'beta'

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.MakeMachineImages(self.messages, self.api_version)[0]],
    ])
    self.Run("""
        compute machine-images describe machine-image-1
        """)

    self.CheckRequests(
        [(self.compute.machineImages, 'Get',
          self.messages.ComputeMachineImagesGetRequest(
              machineImage='machine-image-1', project='my-project'))],)
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            description: Machine Image 1
            name: machine-image-1
            selfLink: https://compute.googleapis.com/compute/{api_version}/projects/my-project/global/machineImages/machine-image-1
            sourceInstanceProperties:
              disks:
              - autoDelete: true
                boot: true
                deviceName: device-1
                mode: READ_WRITE
                source: disk-1
                type: PERSISTENT
              - autoDelete: true
                boot: true
                deviceName: device-2
                mode: READ_ONLY
                type: SCRATCH
              machineType: n1-standard-1
            status: READY
            """.format(api_version=self.api_version)))


class MachineImagesDescribeTestAlpha(MachineImagesDescribeTestBeta):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
