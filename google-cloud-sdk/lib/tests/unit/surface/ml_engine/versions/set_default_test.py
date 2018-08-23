# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""ml-engine versions set-default tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import versions_api
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


class SetDefaultTestBase(object):

  def SetUp(self):
    self.version_ref = resources.REGISTRY.Parse(
        'versionId',
        params={'projectsId': self.Project(), 'modelsId': 'modelId'},
        collection='ml.projects.models.versions')

  def testSetDefault(self):
    self.Run('ml-engine versions set-default versionId --model modelId')

    self.set_default_mock.assert_called_once_with(self.version_ref)


class SetDefaultGaTest(SetDefaultTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    resources.REGISTRY.RegisterApiByName('ml', 'v1')
    super(SetDefaultGaTest, self).SetUp()
    self.set_default_mock = self.StartObjectPatch(
        versions_api.VersionsClient, 'SetDefault',
        return_value=self.short_msgs.Version(name='versionName'))


class SetDefaultBetaTest(SetDefaultTestBase, base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(SetDefaultBetaTest, self).SetUp()
    self.set_default_mock = self.StartObjectPatch(
        versions_api.VersionsClient, 'SetDefault',
        return_value=self.short_msgs.Version(name='versionName'))


if __name__ == '__main__':
  test_case.main()
