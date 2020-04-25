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
"""Tests for 'multiclusteringress enable' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from tests.lib import test_case
from tests.lib.surface.container.hub.features import base


class EnableTest(base.FeaturesTestBase):
  """Tests for the logic of 'ingress enable' command.
  """

  FEATURE_NAME = 'multiclusteringress'
  FEATURE_DISPLAY_NAME = 'Ingress'
  NO_FEATURE_PREFIX = 'ingress'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _ExpectCreateCalls(self, config_membership_id):
    config_membership = '{0}/memberships/{1}'.format(
        self.memberships_api.parent, config_membership_id)
    feature = self.features_api._MakeFeature(
        multiclusteringressFeatureSpec=
        self.features_api.messages.MultiClusterIngressFeatureSpec(
            configMembership=config_membership))

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

    code = self.features_api.messages.FeatureStateDetails.CodeValueValuesEnum.OK
    details = self.features_api.messages.FeatureStateDetails(code=code)
    feature_copy = self.features_api._MakeFeature(
        featureState=self.features_api.messages.FeatureState(details=details),
        multiclusteringressFeatureSpec=
        self.features_api.messages.MultiClusterIngressFeatureSpec(
            configMembership=config_membership))
    self.features_api.ExpectGet(feature_copy)

  def testEnableWithNoMemberships(self):
    self.memberships_api.ExpectList(responses=[])
    with self.AssertRaisesExceptionMatches(exceptions.Error, 'No Memberships'):
      self.RunCommand(['enable'])

  def testEnableWithConfigMembership(self):
    config_membership_id = 'golden-cluster'
    self._ExpectCreateCalls(config_membership_id)
    self.RunCommand(['enable', '--config-membership={0}'.format(
        config_membership_id)])

  def testEnableWithoutConfigMembership(self):
    config_membership_id = 'golden-cluster'
    self.memberships_api.ExpectList([self.memberships_api._MakeMembership(
        name=config_membership_id, description=config_membership_id)])
    self.WriteInput('1')
    self._ExpectCreateCalls(config_membership_id)
    self.RunCommand(['enable'])


if __name__ == '__main__':
  test_case.main()
