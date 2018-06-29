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

"""Tests that exercise describing iOS versions in the device catalog."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core.console import console_attr
from tests.lib import test_case
from tests.lib.surface.firebase.test import test_utils
from tests.lib.surface.firebase.test.ios import commands
from tests.lib.surface.firebase.test.ios import fake_catalogs
from tests.lib.surface.firebase.test.ios import unit_base


class TestIosVersionsDescribeTest(unit_base.IosMockClientTest):

  def SetUp(self):
    console_attr.GetConsoleAttr(encoding='ascii')

  def TearDown(self):
    console_attr.ResetConsoleAttr()

  def testIosVersionsDescribe_VersionNotFound(self):
    self.ExpectIosCatalogGet(fake_catalogs.FakeIosCatalog())

    with self.assertRaises(exceptions.VersionNotFoundError):
      self.Run(commands.IOS_VERSIONS_DESCRIBE + 'bad-version')

    self.AssertErrContains("'bad-version' is not a valid OS version")

  def testIosVersionsDescribe_VersionFound(self):
    self.ExpectIosCatalogGet(fake_catalogs.FakeIosCatalog())
    self.Run(commands.IOS_VERSIONS_DESCRIBE + '6.0')

    self.AssertOutputContains("id: '6.0'")
    self.AssertOutputContains('majorVersion: 6')
    self.AssertOutputContains('minorVersion: 0')
    self.AssertOutputContains('tags:\n- default')

  def testIosVersionsDescribe_ApiThrowsHttpError(self):
    err = test_utils.MakeHttpError('Error9', 'Environment catalog failure.')
    self.ExpectIosCatalogGetError(err)

    with self.assertRaises(calliope_exceptions.HttpException):
      self.Run(commands.IOS_VERSIONS_DESCRIBE + '5.1')

    self.AssertOutputEquals('')
    self.AssertErrMatches(r'(gcloud.*firebase.test.ios.versions.describe)')
    self.AssertErrContains('Environment catalog failure.')


if __name__ == '__main__':
  test_case.main()
