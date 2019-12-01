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
"""Tests for 'multiclusteringress describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import yaml
from tests.lib import test_case
from tests.lib.surface.container.hub.features import base


class DescribeTest(base.FeaturesTestBase):
  """Tests for the logic of 'multiclusteringress describe' command.
  """

  FEATURE_NAME = 'multiclusteringress'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _MakeMultiClusterIngressFeatureSpec(self, config_membership):
    return self.features_api.messages.MultiClusterIngressFeatureSpec(
        configMembership=config_membership)

  def _MakeFeatureState(self, lifecycle_state):
    return self.features_api.messages.FeatureState(
        lifecycleState=lifecycle_state)

  def testRunDescribe(self):
    config_membership = '{0}/memberships/golden-cluster'.format(
        self.features_api.parent)
    lifecycle_state = (self.features_api.messages.FeatureState
                       .LifecycleStateValueValuesEnum.ENABLED)
    multiclusteringress_feature_spec = self._MakeMultiClusterIngressFeatureSpec(
        config_membership=config_membership)
    feature = self.features_api._MakeFeature(
        multiclusteringressFeatureSpec=multiclusteringress_feature_spec,
        featureState=self._MakeFeatureState(lifecycle_state))
    self.features_api.ExpectGet(feature)

    self.RunCommand(['describe'])

    out = yaml.load(self.GetOutput())
    self.assertIsNotNone(out)
    kwargs = {
        'multiclusteringressFeatureSpec': {
            'configMembership': config_membership
        },
        'featureState': {
            'lifecycleState': lifecycle_state.name
        }
    }
    self.assertEqual(out, kwargs)


if __name__ == '__main__':
  test_case.main()
