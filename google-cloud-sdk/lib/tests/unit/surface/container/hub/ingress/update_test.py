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
"""Tests for 'multiclusteringress update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from tests.lib import test_case
from tests.lib.surface.container.hub.features import base


class UpdateTest(base.FeaturesTestBase):
  """Tests for the logic of 'ingress update' command.
  """

  FEATURE_NAME = 'multiclusteringress'
  FEATURE_DISPLAY_NAME = 'Ingress'
  NO_FEATURE_PREFIX = 'ingress'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _ExpectUpdateCalls(self, config_membership_id):
    config_membership = '{0}/memberships/{1}'.format(
        self.memberships_api.parent, config_membership_id)
    feature = self.features_api._MakeFeature(
        multiclusteringressFeatureSpec=
        self.features_api.messages.MultiClusterIngressFeatureSpec(
            configMembership=config_membership))

    operation = self.features_api._MakeOperation()
    mask = 'multiclusteringress_feature_spec.config_membership'
    self.features_api.ExpectUpdate(mask, feature, operation)
    self.features_api.ExpectOperation(operation)
    response = encoding.PyValueToMessage(
        self.features_api.messages.Operation.ResponseValue, {
            'name': self.features_api.resource_name,
        })
    operation = self.features_api._MakeOperation(done=True, response=response)
    self.features_api.ExpectOperation(operation)
    self.features_api.ExpectGet(feature)

  def testCancelUpdate(self):
    self.WriteInput('n')
    with self.AssertRaisesExceptionMatches(exceptions.Error, 'Aborted by user'):
      self.RunCommand(['update'])

  def testUpdateWithNoMemberships(self):
    self.WriteInput('y')
    self.memberships_api.ExpectList(responses=[])
    with self.AssertRaisesExceptionMatches(exceptions.Error, 'No Memberships'):
      self.RunCommand(['update'])

  def testUpdateWithConfigMembership(self):
    self.WriteInput('y')
    config_membership_id = 'golden-cluster'
    self._ExpectUpdateCalls(config_membership_id)
    self.RunCommand(['update', '--config-membership={0}'.format(
        config_membership_id)])

  def testUpdateWithoutConfigMembership(self):
    self.WriteInput('y')
    config_membership_id = 'golden-cluster'
    self.memberships_api.ExpectList([self.memberships_api._MakeMembership(
        name=config_membership_id, description=config_membership_id)])
    self.WriteInput('1')
    self._ExpectUpdateCalls(config_membership_id)
    self.RunCommand(['update'])


if __name__ == '__main__':
  test_case.main()
