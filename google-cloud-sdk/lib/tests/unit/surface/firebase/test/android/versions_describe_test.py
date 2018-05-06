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

"""Tests that exercise describing Android OS versions in the device catalog."""

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core.console import console_attr
from tests.lib import test_case
from tests.lib.surface.firebase.test import test_utils
from tests.lib.surface.firebase.test.android import commands
from tests.lib.surface.firebase.test.android import fake_catalogs
from tests.lib.surface.firebase.test.android import unit_base


class TestVersionsDescribeTest(unit_base.AndroidMockClientTest):

  def SetUp(self):
    console_attr.GetConsoleAttr(encoding='ascii')

  def TearDown(self):
    console_attr.ResetConsoleAttr()

  def testVersionsDescribe_VersionNotFound(self):
    self.ExpectCatalogGet(fake_catalogs.FakeAndroidCatalog())

    with self.assertRaises(exceptions.VersionNotFoundError):
      self.Run(commands.ANDROID_VERSIONS_DESCRIBE + 'bad-version')

    self.AssertErrContains("'bad-version' is not a valid OS version")

  def testVersionsDescribe_VersionFound(self):
    self.ExpectCatalogGet(fake_catalogs.FakeAndroidCatalog())
    self.Run(commands.ANDROID_VERSIONS_DESCRIBE + 'C')

    self.AssertOutputContains('apiLevel: 3')
    self.AssertOutputContains('codeName: Cupcake')
    self.AssertOutputContains('distribution:\n  marketShare: 12.3')
    self.AssertOutputContains('id: C')
    self.AssertOutputContains('releaseDate:\n  day: 27\n  month: 4')
    self.AssertOutputContains("versionString: '1.5'")
    self.AssertOutputContains('tags:\n- unsupported\n- deprecated')

  def testVersionsDescribe_ApiThrowsHttpError(self):
    err = test_utils.MakeHttpError('Error9', 'Environment catalog failure.')
    self.ExpectCatalogGetError(err)

    with self.assertRaises(calliope_exceptions.HttpException):
      self.Run(commands.ANDROID_VERSIONS_DESCRIBE + 'F')

    self.AssertOutputEquals('')
    self.AssertErrMatches(r'(gcloud.*.test.android.versions.describe)')
    self.AssertErrContains('Environment catalog failure.')


if __name__ == '__main__':
  test_case.main()
