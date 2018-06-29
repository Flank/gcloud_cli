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

"""Gcloud tests that exercise device catalog OS version listing."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.console import console_attr
from tests.lib import test_case
from tests.lib.surface.firebase.test import test_utils
from tests.lib.surface.firebase.test.android import commands
from tests.lib.surface.firebase.test.android import fake_catalogs
from tests.lib.surface.firebase.test.android import unit_base


class TestAndroidVersionsListTest(unit_base.AndroidMockClientTest):

  def SetUp(self):
    console_attr.GetConsoleAttr(encoding='ascii')

  def testAndroidVersionsList_NoVersionsFound(self):
    self.ExpectCatalogGet(fake_catalogs.EmptyAndroidCatalog())
    self.Run(commands.ANDROID_VERSIONS_LIST)
    self.AssertErrContains('Listed 0 items.')

  def testAndroidVersionsList_TwoVersionsFound(self):
    self.ExpectCatalogGet(fake_catalogs.FakeAndroidCatalog())
    self.Run(commands.ANDROID_VERSIONS_LIST)
    self.AssertOutputContains(
        """\
        | C | 1.5 | Cupcake | 3 | 2009-04-27 | unsupported,deprecated |
        | F | 2.2.x | Froyo | 8 | 2010-05-10 | default |""",
        normalize_space=True)

  def testAndroidVersionsList_ApiThrowsHttpError(self):
    err = test_utils.MakeHttpError('Error9', 'Environment catalog failure.')
    self.ExpectCatalogGetError(err)

    with self.assertRaises(exceptions.HttpException):
      self.Run(commands.ANDROID_VERSIONS_LIST)

    self.AssertOutputEquals('')
    self.AssertErrContains('(gcloud.firebase.test.android.versions.list)')
    self.AssertErrContains('Environment catalog failure.')


if __name__ == '__main__':
  test_case.main()
