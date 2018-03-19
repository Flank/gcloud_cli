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

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.console import console_attr
from tests.lib import test_case
from tests.lib.surface.firebase.test import commands
from tests.lib.surface.firebase.test import unit_base


TESTING_V1_MESSAGES = apis.GetMessagesModule('testing', 'v1')

_ANDROID_VERSION_2 = TESTING_V1_MESSAGES.AndroidVersion(
    id='e',
    apiLevel=2,
    versionString='2.7.x',
    codeName='Icee',
    distribution=TESTING_V1_MESSAGES.Distribution(marketShare=0.0271828),
    releaseDate=TESTING_V1_MESSAGES.Date(year=2012, month=2, day=7),
    tags=['id'])

_ANDROID_VERSION_3 = TESTING_V1_MESSAGES.AndroidVersion(
    id='pi',
    apiLevel=3,
    versionString='3.1.x',
    codeName='Pie',
    distribution=TESTING_V1_MESSAGES.Distribution(marketShare=0.0314159),
    releaseDate=TESTING_V1_MESSAGES.Date(year=2013, month=3, day=14),
    tags=['dog'])

_NO_VERSIONS_CATALOG = TESTING_V1_MESSAGES.AndroidDeviceCatalog(versions=[])

_TWO_VERSIONS_CATALOG = TESTING_V1_MESSAGES.AndroidDeviceCatalog(
    versions=[_ANDROID_VERSION_2, _ANDROID_VERSION_3])


class TestVersionsListTest(unit_base.TestMockClientTest):

  def SetUp(self):
    console_attr.GetConsoleAttr(encoding='ascii')

  def testVersionsList_NoVersionsFound(self):
    self.ExpectCatalogGet(_NO_VERSIONS_CATALOG)
    self.Run(commands.ANDROID_VERSIONS_LIST)
    self.AssertErrContains('Listed 0 items.')

  def testVersionsList_TwoVersionsFound(self):
    self.ExpectCatalogGet(_TWO_VERSIONS_CATALOG)
    self.Run(commands.ANDROID_VERSIONS_LIST)
    self.AssertOutputContains("""\
        | e | 2.7.x | Icee | 2 | 2012-02-07 | id |
        | pi | 3.1.x | Pie | 3 | 2013-03-14 | dog |""", normalize_space=True)

  def testVersionsList_ApiThrowsHttpError(self):
    err = unit_base.MakeHttpError('Error9', 'Environment catalog failure.')
    self.ExpectCatalogGetError(err)

    with self.assertRaises(exceptions.HttpException):
      self.Run(commands.ANDROID_VERSIONS_LIST)

    self.AssertOutputEquals('')
    self.AssertErrMatches(r'(gcloud.*.test.*versions\.list)')
    self.AssertErrContains('Environment catalog failure.')


if __name__ == '__main__':
  test_case.main()
