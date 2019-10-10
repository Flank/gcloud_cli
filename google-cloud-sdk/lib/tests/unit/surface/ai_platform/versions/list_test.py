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
"""ai-platform versions list tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import versions_api
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


@parameterized.parameters('ml-engine', 'ai-platform')
class ListTestBase(object):

  def SetUp(self):
    self.model_ref = resources.REGISTRY.Parse(
        'modelId', params={'projectsId': self.Project()},
        collection='ml.projects.models')
    self.list_mock = self.StartObjectPatch(
        versions_api.VersionsClient, 'List',
        return_value=iter([
            self.short_msgs.Version(
                name='v1',
                deploymentUri='gs://foo/bar/',
                state=self.short_msgs.Version.StateValueValuesEnum.READY),
            self.short_msgs.Version(
                name='v2',
                deploymentUri='gs://baz/qux/',
                state=self.short_msgs.Version.StateValueValuesEnum.UNKNOWN)]))

  def testList(self, module_name):
    self.Run('{} versions list --model modelId'.format(module_name))

    self.list_mock.assert_called_once_with(self.model_ref)
    self.AssertOutputContains('v1')
    self.AssertOutputContains('v2')

  def testList_TestFormat(self, module_name):
    self.Run('{} versions list --model modelId'.format(module_name))

    self.list_mock.assert_called_once_with(self.model_ref)
    self.AssertOutputEquals("""\
        NAME  DEPLOYMENT_URI  STATE
        v1    gs://foo/bar/   READY
        v2    gs://baz/qux/   UNKNOWN
        """, normalize_space=True)


class ListGaTest(ListTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    resources.REGISTRY.RegisterApiByName('ml', 'v1')
    super(ListGaTest, self).SetUp()


class ListBetaTest(ListTestBase, base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(ListBetaTest, self).SetUp()


if __name__ == '__main__':
  test_case.main()
