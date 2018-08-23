# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Test of the 'describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bigtable import app_profiles
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib.surface.bigtable import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA)
class AppProfileDescribeTests(base.BigtableV2TestBase):

  def SetUp(self):
    self.app_profile_ref = util.GetAppProfileRef('my-instance',
                                                 'my-app-profile')
    self.app_profile_describe_mock = self.StartObjectPatch(
        app_profiles,
        'Describe',
        return_value=self.msgs.AppProfile(name='my-app-profile'))

  def testDescribe(self, track):
    self.track = track
    self.Run('bigtable app-profiles describe my-app-profile '
             '--instance my-instance')
    self.app_profile_describe_mock.assert_called_once_with(self.app_profile_ref)
