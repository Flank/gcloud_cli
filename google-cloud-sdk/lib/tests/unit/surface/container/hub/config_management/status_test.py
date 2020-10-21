# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Tests for 'config-management status' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from tests.lib import test_case
from tests.lib.surface.container.hub.features import base


class StatusTest(base.FeaturesTestBase):
  """Tests for the logic of 'config-management status' command."""

  FEATURE_NAME = 'configmanagement'
  FEATURE_DISPLAY_NAME = 'Config Management'
  NO_FEATURE_PREFIX = 'config-management'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _MakeConfigmanagementFeatureSpec(self):
    return self.features_api.messages.ConfigmanagementFeatureSpec()

  def _MakeFeatureState(self, lifecycle_state, details_by_membership):
    return self.features_api.messages.FeatureState(
        lifecycleState=lifecycle_state,
        detailsByMembership=details_by_membership)

  def testRunStatus(self):
    cluster_name = 'mock-cluster'
    msg = self.features_api.messages
    msg_fs = self.features_api.messages.FeatureState
    lifecycle_state = (
        msg_fs.LifecycleStateValueValuesEnum
        .ENABLED)
    details_by_membership = (msg_fs.DetailsByMembershipValue(
        additionalProperties=[msg_fs.DetailsByMembershipValue.AdditionalProperty(
            key='projects/mock-project/locations/global/memberships/mock-cluster',
            value=msg.FeatureStateDetails(
                configmanagementFeatureState=msg.ConfigManagementFeatureState(
                    clusterName=cluster_name)))]))
    feature = self.features_api._MakeFeature(
        configmanagementFeatureSpec=self.features_api.messages
        .ConfigManagementFeatureSpec(),
        featureState=self._MakeFeatureState(lifecycle_state,
                                            details_by_membership))
    self.features_api.ExpectGet(feature)
    self.memberships_api.ExpectList([self.memberships_api._MakeMembership(
        name='mock-cluster', description='config_membership')])

    self.RunCommand(['status'])
    out = yaml.load(self.GetOutput())
    self.assertIsNotNone(out)
    split_out = out.split()
    log.warning(split_out)
    header = ['Name', 'Status', 'Last_Synced_Token', 'Sync_Branch',
              'Last_Synced_Time', 'Policy_Controller']
    for i, _ in enumerate(header):
      self.assertEqual(split_out[i], header[i])
    self.assertEqual(split_out[len(header)], cluster_name)


if __name__ == '__main__':
  test_case.main()
