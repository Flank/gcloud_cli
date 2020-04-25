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
"""Tests for 'config-management enable' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.container.hub.features import base


class EnableTest(base.FeaturesTestBase):
  """Tests for the logic of 'config-management enable' command."""

  FEATURE_NAME = 'configmanagement'
  FEATURE_DISPLAY_NAME = 'Config Management'
  NO_FEATURE_PREFIX = 'config-management'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _ExpectCreateCalls(self):
    feature = self.features_api._MakeFeature(
        configmanagementFeatureSpec=self.features_api.messages
        .ConfigManagementFeatureSpec(
            membershipConfigs=self.features_api.messages
            .ConfigManagementFeatureSpec.MembershipConfigsValue(
                additionalProperties=[])))

    operation = self.features_api._MakeOperation()
    self.features_api.ExpectCreate(feature, operation)
    self.features_api.ExpectOperation(operation)
    response = encoding.PyValueToMessage(
        self.features_api.messages.Operation.ResponseValue, {
            'name': self.features_api.resource_name,
        })
    operation = self.features_api._MakeOperation(done=True, response=response)
    self.features_api.ExpectOperation(operation)
    self.features_api.ExpectGet(feature)
    self.features_api.ExpectOperation(operation)

  def testEnable(self):
    self._ExpectCreateCalls()
    self.RunCommand(['enable'])


if __name__ == '__main__':
  test_case.main()
