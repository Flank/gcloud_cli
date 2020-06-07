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
"""Tests for the instances get-screenshot subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import os

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base

_BASE_64_JPEG = ('/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQE'
                 'BAgGBgUGCQgKCgkICQkKDA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD/'
                 '2wBDAQMDAwQDBAgEBAgQCwkLEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQ'
                 'EBAQEBAQEBAQEBAQEBAQEBAQEBAQEBD/wAARCAAKAAoDASIAAhEBAxEB/8QA'
                 'FgABAQEAAAAAAAAAAAAAAAAACAYH/8QAIBAAAwEAAgIDAQEAAAAAAAAAAQID'
                 'BAURBxMABiESQf/EABUBAQEAAAAAAAAAAAAAAAAAAAUG/8QAIhEAAgEDAgcA'
                 'AAAAAAAAAAAAAQIRAwQSIUEABQYxUWHR/9oADAMBAAIRAxEAPwA2bPG/27Tx'
                 '8+Ky8lqycdg06KcXl9+jKkMWXQjZ2cvJapQ1mEWnsb1St7e2P9vanyeS/vT5'
                 'YvDidmmTTUpaMORdKL1+MrS4rTMgj9BTRdSD+VqOnbGfAN7cx468u8py1n27'
                 'ePwrzWTTpY0rn5AQ2MNc3bspcEA+wEN2Ae/h/ve2m1NOmz1rVi9KOxZnYnsk'
                 'k/pJP+/DLazWkSJMHwSIiBsd+/3i4511HWvqVNwihkABLKj5Z5OJyUxjJUej'
                 'pjrP/9k=')


class InstancesGetScreenshotBetaTest(test_base.BaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def SetUp(self):
    self.SelectApi(self.api_version)
    self.make_requests.side_effect = [[
        self.messages.Screenshot(
            kind='compute#screenshot', contents=_BASE_64_JPEG)
    ]]
    self.output_path = os.path.join(self.temp_path, 'output.jpg')

  def testGetScreenShotToFile(self):
    self.Run(
        'compute instances get-screenshot my-instance --zone=test-zone --destination={}'
        .format(self.output_path))

    self.CheckRequests([(self.compute.instances, 'GetScreenshot',
                         self.messages.ComputeInstancesGetScreenshotRequest(
                             instance='my-instance',
                             zone='test-zone',
                             project='my-project'))])
    self.AssertFileExists(self.output_path)

  def testGetScreenShotToStdOut(self):
    self.Run('compute instances get-screenshot my-instance --zone=test-zone')

    self.CheckRequests([(self.compute.instances, 'GetScreenshot',
                         self.messages.ComputeInstancesGetScreenshotRequest(
                             instance='my-instance',
                             zone='test-zone',
                             project='my-project'))])
    self.AssertOutputBytesEquals(base64.b64decode(_BASE_64_JPEG))

if __name__ == '__main__':
  test_case.main()

