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
"""Test of the 'list' command."""

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
class AppProfileListTests(base.BigtableV2TestBase):

  def SetUp(self):
    self.app_profile_list_mock = self.StartObjectPatch(
        app_profiles,
        'List',
        return_value=[
            self.msgs.AppProfile(
                name='app-profile-1',
                description='dsp1',
                multiClusterRoutingUseAny=self.msgs.MultiClusterRoutingUseAny()
            ),
            self.msgs.AppProfile(
                name='app-profile-2',
                description='dsp2',
                singleClusterRouting=self.msgs.SingleClusterRouting(
                    clusterId='my-cluster', allowTransactionalWrites=False)),
            self.msgs.AppProfile(
                name='app-profile-3',
                description='dsp3',
                singleClusterRouting=self.msgs.SingleClusterRouting(
                    clusterId='my-cluster-2', allowTransactionalWrites=True)),
        ])

  def testList(self, track):
    self.track = track
    self.Run('bigtable app-profiles list --instance my-instance')
    self.app_profile_list_mock.assert_called_once_with(
        util.GetInstanceRef('my-instance'))
    self.AssertOutputContains(
        """\
NAME DESCRIPTION ROUTING TRANSACTIONAL_WRITES
app-profile-1 dsp1 MULTI_CLUSTER_USE_ANY No
app-profile-2 dsp2 my-cluster No
app-profile-3 dsp3 my-cluster-2 Yes
""",
        normalize_space=True)
