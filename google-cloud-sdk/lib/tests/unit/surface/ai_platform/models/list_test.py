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
"""ai-platform models list tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import models
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


@parameterized.parameters('ml-engine', 'ai-platform')
class ListTestBase(object):

  def _MakeTestModels(self):
    return [
        self.short_msgs.Model(
            name='projects/{}/models/modelName1'.format(self.Project()),
            defaultVersion=self.short_msgs.Version(name='v1')),
        self.short_msgs.Model(
            name='projects/{}/models/modelName2'.format(self.Project()),
            defaultVersion=self.short_msgs.Version(name='v2'))]

  def testList(self, module_name):
    self.Run('{} models list'.format(module_name))

    project_ref = resources.REGISTRY.Parse(self.Project(),
                                           collection='ml.projects')
    self.mocked.assert_called_once_with(project_ref)
    self.AssertOutputContains('modelName1')
    self.AssertOutputContains('modelName2')
    self.AssertOutputEquals("""\
        NAME       DEFAULT_VERSION_NAME
        modelName1 v1
        modelName2 v2
        """, normalize_space=True)

  def testList_Uri(self, module_name):
    self.Run('{} models list --uri'.format(module_name))

    project_ref = resources.REGISTRY.Parse(self.Project(),
                                           collection='ml.projects')
    self.mocked.assert_called_once_with(project_ref)
    self.AssertOutputEquals("""\
        https://ml.googleapis.com/v1/projects/fake-project/models/modelName1
        https://ml.googleapis.com/v1/projects/fake-project/models/modelName2
        """, normalize_space=True)


class ListGaTest(ListTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    self.mocked = self.StartObjectPatch(
        models.ModelsClient, 'List',
        return_value=iter(self._MakeTestModels()))


class ListBetaTest(ListTestBase, base.MlBetaPlatformTestBase):

  def SetUp(self):
    self.mocked = self.StartObjectPatch(
        models.ModelsClient, 'List',
        return_value=iter(self._MakeTestModels()))


if __name__ == '__main__':
  test_case.main()
