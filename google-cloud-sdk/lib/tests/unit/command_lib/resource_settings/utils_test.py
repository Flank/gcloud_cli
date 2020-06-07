# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for Org Policy command utilities module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.resource_settings import arguments
from googlecloudsdk.command_lib.resource_settings import utils
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.calliope import util as calliope_util


class UtilsTest(cli_test_base.CliTestBase):

  RESOURCE_FLAG = '--organization'
  RESOURCE_ID = '12345678'
  SETTING_WITHOUT_PREFIX = 'iam-projectCreatorRoles'
  SETTING_WITH_PREFIX = 'settings/iam-projectCreatorRoles'
  SETTING_NAME = 'organizations/12345678/policies/testService.testRestriction'

  def SetUp(self):
    self.parser = calliope_util.ArgumentParser()
    arguments.AddSettingsNameArgToParser(self.parser)
    arguments.AddResourceFlagsToParser(self.parser)

  def testGetSettingFromArgs_SettingPrefixNotPresent_AddsPrefix(self):
    args = self.parser.parse_args(
        [self.SETTING_WITHOUT_PREFIX, self.RESOURCE_FLAG, self.RESOURCE_ID])

    setting = utils.GetSettingFromArgs(args)

    self.assertEqual(setting, self.SETTING_WITH_PREFIX)

  def testGetSettingFromArgs_SettingPrefixPresent_SkipsAddingPrefix(self):
    args = self.parser.parse_args(
        [self.SETTING_WITH_PREFIX, self.RESOURCE_FLAG, self.RESOURCE_ID])

    setting = utils.GetSettingFromArgs(args)

    self.assertEqual(setting, self.SETTING_WITH_PREFIX)

  def testGetSettingNameFromArgs_SettingPrefixNotPresent_SkipsRemovingPrefix(
      self):
    args = self.parser.parse_args(
        [self.SETTING_WITHOUT_PREFIX, self.RESOURCE_FLAG, self.RESOURCE_ID])

    setting = utils.GetSettingNameFromArgs(args)

    self.assertEqual(setting, self.SETTING_WITHOUT_PREFIX)

  def testGetSettingNameFromArgs_SettingPrefixPresent_RemovesPrefix(self):
    args = self.parser.parse_args(
        [self.SETTING_WITHOUT_PREFIX, self.RESOURCE_FLAG, self.RESOURCE_ID])

    setting = utils.GetSettingNameFromArgs(args)

    self.assertEqual(setting, self.SETTING_WITHOUT_PREFIX)


if __name__ == '__main__':
  test_case.main()
