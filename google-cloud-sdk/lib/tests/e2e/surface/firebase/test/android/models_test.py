# Copyright 2017 Google Inc. All Rights Reserved.
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

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.firebase.test import e2e_base
from tests.lib.surface.firebase.test.android import commands

_PROJECT_ARG = ' --project cloud-sdk-integration-testing'


class AndroidModelsTests(e2e_base.TestIntegrationTestBase):

  def testAndroidModelsListWithValidProject(self):
    # Fetch the catalog with an explicit, known-good project specified to verify
    # that the IAM check for GetTestEnvironmentCatalog works correctly.
    self.Run(commands.ANDROID_MODELS_LIST + _PROJECT_ARG)
    self.AssertOutputMatches(r'^MODEL_ID | MAKE | MODEL', normalize_space=True)
    self.AssertOutputMatches(r'Nexus.* VIRTUAL')
    self.AssertOutputContains('default')
    self.AssertOutputContains('PHYSICAL')

  def testAndroidModelsListWithNoProjectSpecified(self):
    # Mock out properties so that core.project appears to not be set by user.
    # This verifies that the IAM check for GetTestEnvironmentCatalog is skipped
    # when no project is given, and the GA catalog is still available.
    self.prop_mock = self.StartObjectPatch(properties.VALUES.core.project,
                                           'Get')
    self.prop_mock.return_value = None

    self.Run(commands.ANDROID_MODELS_LIST)

    self.AssertOutputMatches(r'^MODEL_ID | MAKE | MODEL', normalize_space=True)
    self.AssertOutputMatches(r'Nexus.* VIRTUAL')
    self.AssertOutputContains('default')
    self.AssertOutputContains('PHYSICAL')

  def testAndroidModelsDescribePhysical(self):
    self.Run(commands.ANDROID_MODELS_DESCRIBE + 'hammerhead')
    self.AssertOutputContains('id: hammerhead')
    self.AssertOutputContains('name: Nexus 5')
    self.AssertOutputContains('brand: LG')
    self.AssertOutputContains('form: PHYSICAL')
    self.AssertOutputContains('screenY: 1920')

  def testAndroidModelsDescribeVirtual(self):
    self.Run(commands.ANDROID_MODELS_DESCRIBE + 'Nexus6P')
    self.AssertOutputContains('id: Nexus6P')
    self.AssertOutputContains('name: Nexus 6P')
    self.AssertOutputContains('brand: Google')
    self.AssertOutputContains('manufacturer: Google')
    self.AssertOutputContains('form: VIRTUAL')
    self.AssertOutputContains('screenDensity: 518')


if __name__ == '__main__':
  test_case.main()
