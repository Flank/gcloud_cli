# -*- coding: utf-8 -*- #
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

"""Gcloud tests that exercise device catalog locale listing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.console import console_attr
from tests.lib import test_case
from tests.lib.surface.firebase.test import test_utils
from tests.lib.surface.firebase.test.android import commands
from tests.lib.surface.firebase.test.android import unit_base


TESTING_MESSAGES = apis.GetMessagesModule('testing', 'v1')


_LOCALE_1 = TESTING_MESSAGES.Locale(
    id='en_FD',
    name='English',
    region='Federation',
    tags=['Kirk', 'Spock'])

_LOCALE_2 = TESTING_MESSAGES.Locale(
    id='kl',
    name='Klingon',
    region='Empire')

_LOCALE_3 = TESTING_MESSAGES.Locale(
    id='fe',
    name='Ferengi',
    region='Alliance')

_NO_LOCALES_CATALOG = TESTING_MESSAGES.AndroidDeviceCatalog(
    runtimeConfiguration=TESTING_MESSAGES.AndroidRuntimeConfiguration(
        locales=[]))

_THREE_LOCALES_CATALOG = TESTING_MESSAGES.AndroidDeviceCatalog(
    runtimeConfiguration=TESTING_MESSAGES.AndroidRuntimeConfiguration(
        locales=[_LOCALE_1, _LOCALE_2, _LOCALE_3]))


class TestAndroidLocalesListTest(unit_base.AndroidMockClientTest):

  def SetUp(self):
    console_attr.GetConsoleAttr(encoding='ascii')

  def testAndroidLocalesList_NoLocalesFound(self):
    self.ExpectCatalogGet(_NO_LOCALES_CATALOG)
    self.Run(commands.ANDROID_LOCALES_LIST)
    self.AssertErrContains('Listed 0 items.')

  def testAndroidLocalesList_TwoLocalesFound(self):
    self.ExpectCatalogGet(_THREE_LOCALES_CATALOG)
    self.Run(commands.ANDROID_LOCALES_LIST)
    self.AssertOutputContains("""\
        | en_FD | English | Federation | Kirk,Spock |
        | kl | Klingon | Empire | |
        | fe | Ferengi | Alliance | |""", normalize_space=True)

  def testAndroidLocalesList_ApiThrowsHttpError(self):
    err = test_utils.MakeHttpError('Failure 3', 'Environment catalog missing.')
    self.ExpectCatalogGetError(err)

    with self.assertRaises(exceptions.HttpException):
      self.Run(commands.ANDROID_LOCALES_LIST)

    self.AssertOutputEquals('')
    self.AssertErrMatches(r'(gcloud.*.test.*locales\.list)')
    self.AssertErrContains('Environment catalog missing.')


if __name__ == '__main__':
  test_case.main()
