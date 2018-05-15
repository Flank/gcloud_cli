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

"""Tests that exercise describing Android models in the device catalog."""

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core.console import console_attr
from tests.lib import test_case
from tests.lib.surface.firebase.test import test_utils
from tests.lib.surface.firebase.test.android import commands
from tests.lib.surface.firebase.test.android import fake_catalogs
from tests.lib.surface.firebase.test.android import unit_base


class TestAndroidModelsDescribeTest(unit_base.AndroidMockClientTest):

  def SetUp(self):
    console_attr.GetConsoleAttr(encoding='ascii')

  def TearDown(self):
    console_attr.ResetConsoleAttr()

  def testAndroidModelsDescribe_ModelNotFound(self):
    self.ExpectCatalogGet(fake_catalogs.FakeAndroidCatalog())

    with self.assertRaises(exceptions.ModelNotFoundError):
      self.Run(commands.ANDROID_MODELS_DESCRIBE + 'bad-model')

    self.AssertErrContains("'bad-model' is not a valid model")

  def testAndroidModelsDescribe_ModelFound(self):
    self.ExpectCatalogGet(fake_catalogs.FakeAndroidCatalog())
    self.Run(commands.ANDROID_MODELS_DESCRIBE + 'Universe3')

    self.AssertOutputContains('brand: Sungsam')
    self.AssertOutputContains('form: PHYSICAL')
    self.AssertOutputContains('id: Universe3')
    self.AssertOutputContains('name: Universe T3')

  def testAndroidModelsDescribe_ApiThrowsHttpError(self):
    err = test_utils.MakeHttpError('ErrorXYZ', 'Environment catalog failure.')
    self.ExpectCatalogGetError(err)

    with self.assertRaises(calliope_exceptions.HttpException):
      self.Run(commands.ANDROID_MODELS_DESCRIBE + 'a-model')

    self.AssertOutputEquals('')
    self.AssertErrMatches(r'(gcloud.*.test.android.models.describe)')
    self.AssertErrContains('Environment catalog failure.')


if __name__ == '__main__':
  test_case.main()
