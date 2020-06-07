# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""anthos apply tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.anthos import test_base as anthos_test_base


class ApplyTestBeta(anthos_test_base.PackageUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.test_package = self.Touch(
        os.path.join(self.home_path, 'my-package-dir'),
        name='temp',
        makedirs=True)

  def testApply(self):
    self.Run('anthos apply ~/my-package-dir --project my-project')
    self.refresh_mock.assert_called_once()
    self.AssertValidBinaryCall(
        env={'COBRA_SILENCE_USAGE': 'true', 'GCLOUD_AUTH_PLUGIN': 'true'},
        std_in='{"auth_token": "access_token"}',
        command_args=[
            anthos_test_base._MOCK_ANTHOS_BINARY,
            'apply',
            '-f',
            os.path.expanduser('~/my-package-dir'),
            '--project',
            'my-project'])


class ApplyTestALPHA(ApplyTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

if __name__ == '__main__':
  test_case.main()
