# -*- coding: utf-8 -*- #
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

"""Gcloud tests that exercise device catalog OS version listing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.console import console_attr
from tests.lib import test_case
from tests.lib.surface.firebase.test import test_utils
from tests.lib.surface.firebase.test.ios import commands
from tests.lib.surface.firebase.test.ios import fake_catalogs
from tests.lib.surface.firebase.test.ios import unit_base


class TestIosVersionsListTest(unit_base.IosMockClientTest):

  def SetUp(self):
    console_attr.GetConsoleAttr(encoding='ascii')

  def testIosVersionsList_NoVersionsFound(self):
    self.ExpectIosCatalogGet(fake_catalogs.EmptyIosCatalog())
    self.Run(commands.IOS_VERSIONS_LIST)
    self.AssertErrContains('Listed 0 items.')

  def testIosVersionsList_TwoVersionsFound(self):
    self.ExpectIosCatalogGet(fake_catalogs.FakeIosCatalog())
    self.Run(commands.IOS_VERSIONS_LIST)
    self.AssertOutputContains(
        """\
        | 5.1 | 5 | 1 | old |
        | 6.0 | 6 | 0 | default |
        | 7.2 | 7 | 2 | |""",
        normalize_space=True)

  def testIosVersionsList_ApiThrowsHttpError(self):
    err = test_utils.MakeHttpError('Error9', 'Environment catalog failure.')
    self.ExpectIosCatalogGetError(err)

    with self.assertRaises(exceptions.HttpException):
      self.Run(commands.IOS_VERSIONS_LIST)

    self.AssertOutputEquals('')
    self.AssertErrMatches(r'(gcloud.*firebase.test.ios.versions.list)')
    self.AssertErrContains('Environment catalog failure.')


if __name__ == '__main__':
  test_case.main()
