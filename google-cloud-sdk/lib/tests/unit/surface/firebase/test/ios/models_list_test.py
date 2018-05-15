# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests that exercise listing of iOS models in the device catalog."""

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.console import console_attr
from tests.lib import test_case
from tests.lib.surface.firebase.test import test_utils
from tests.lib.surface.firebase.test.ios import commands
from tests.lib.surface.firebase.test.ios import fake_catalogs
from tests.lib.surface.firebase.test.ios import unit_base


class TestIosModelsListTest(unit_base.IosMockClientTest):

  def SetUp(self):
    console_attr.GetConsoleAttr(encoding='ascii')

  def TearDown(self):
    console_attr.ResetConsoleAttr()

  def testIosModelsList_NoModelsFound(self):
    self.ExpectIosCatalogGet(fake_catalogs.EmptyIosCatalog())
    self.Run(commands.IOS_MODELS_LIST)
    self.AssertErrContains('Listed 0 items.')

  def testIosModelsList_ModelsFound(self):
    self.ExpectIosCatalogGet(fake_catalogs.FakeIosCatalog())
    self.Run(commands.IOS_MODELS_LIST)
    self.AssertOutputContains(
        """\
        | iPen2 | iPen 2 | 5.1,6.0,7.2 | default |
        | iPen3 | iPen 3 | 6.0,7.2 | unstable |""",
        normalize_space=True)

  def testIosModelsList_DeprecationWarningShown(self):
    self.ExpectIosCatalogGet(fake_catalogs.FakeIosCatalog())
    self.Run(commands.IOS_MODELS_LIST)
    self.AssertOutputContains(
        """iPencil1 | iPencil 1 | 5.1,6.0 | deprecated=5.1 |""",
        normalize_space=True)
    self.AssertErrContains('Some devices are deprecated. Learn more')

  def testIosModelsList_ApiThrowsHttpError(self):
    err = test_utils.MakeHttpError('ErrorXYZ', 'Environment catalog failure.')
    self.ExpectIosCatalogGetError(err)

    with self.assertRaises(exceptions.HttpException):
      self.Run(commands.IOS_MODELS_LIST)

    self.AssertOutputEquals('')
    self.AssertErrMatches(r'(gcloud.*.test.ios.models.list)')
    self.AssertErrContains('Environment catalog failure.')


if __name__ == '__main__':
  test_case.main()
