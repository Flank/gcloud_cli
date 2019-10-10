# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests that exercise describing iOS models in the device catalog."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core.console import console_attr
from tests.lib import test_case
from tests.lib.surface.firebase.test import test_utils
from tests.lib.surface.firebase.test.ios import commands
from tests.lib.surface.firebase.test.ios import fake_catalogs
from tests.lib.surface.firebase.test.ios import unit_base


class TestIosModelsDescribeTest(unit_base.IosMockClientTest):

  def SetUp(self):
    console_attr.GetConsoleAttr(encoding='ascii')

  def TearDown(self):
    console_attr.ResetConsoleAttr()

  def testModelsDescribe_ModelNotFound(self):
    self.ExpectIosCatalogGet(fake_catalogs.FakeIosCatalog())

    with self.assertRaises(exceptions.ModelNotFoundError):
      self.Run(commands.IOS_MODELS_DESCRIBE + 'bad-model')

    self.AssertErrContains("'bad-model' is not a valid model")

  def testModelsDescribe_ModelFound(self):
    self.ExpectIosCatalogGet(fake_catalogs.FakeIosCatalog())
    self.Run(commands.IOS_MODELS_DESCRIBE + 'iPen3')

    self.AssertOutputContains('id: iPen3')
    self.AssertOutputContains('name: iPen 3')
    self.AssertOutputContains("supportedVersionIds:\n- '6.0'\n- '7.2'")
    self.AssertOutputContains('tags:\n- unstable')

  def testModelsDescribe_ApiThrowsHttpError(self):
    err = test_utils.MakeHttpError('ErrorXYZ', 'Environment catalog failure.')
    self.ExpectIosCatalogGetError(err)

    with self.assertRaises(calliope_exceptions.HttpException):
      self.Run(commands.IOS_MODELS_DESCRIBE + 'a-model')

    self.AssertOutputEquals('')
    self.AssertErrMatches(r'(gcloud.*.test.ios.models.describe)')
    self.AssertErrContains('Environment catalog failure.')


if __name__ == '__main__':
  test_case.main()
