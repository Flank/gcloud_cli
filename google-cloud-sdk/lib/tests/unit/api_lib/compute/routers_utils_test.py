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
"""Tests for the router utils library."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import routers_utils
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import subtests
from tests.lib import test_case


class ParseModeAlphaTest(subtests.Base):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('compute', 'alpha')
    self.resource_classes = [
        self.messages.RouterBgp, self.messages.RouterBgpPeer]

  def RunSubTest(self, resource_class, arg_mode):
    return routers_utils.ParseMode(resource_class, arg_mode)

  def testParse(self):
    for resource_class in self.resource_classes:
      resource_enum = resource_class.AdvertiseModeValueValuesEnum

      self.Run(resource_enum.DEFAULT, resource_class, 'DEFAULT')
      self.Run(resource_enum.CUSTOM, resource_class, 'CUSTOM')


class ParseGroupsAlphaTest(test_case.Base):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('compute', 'alpha')
    self.resource_classes = [
        self.messages.RouterBgp, self.messages.RouterBgpPeer]

  def testParse(self):
    arg_groups = ['ALL_SUBNETS']
    for resource_class in self.resource_classes:
      resource_enum = resource_class.AdvertisedGroupsValueListEntryValuesEnum
      expected_groups = [resource_enum.ALL_SUBNETS]
      actual_groups = routers_utils.ParseGroups(resource_class, arg_groups)
      self.assertEqual(expected_groups, actual_groups)


class ParseIpRangesAlphaTest(test_case.Base):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('compute', 'alpha')

  def testParse(self):
    arg_ranges = {'10.10.10.10/30': 'custom-range', '10.10.10.20/30': ''}
    expected_ranges = [
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.10/30', description='custom-range'),
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.20/30', description=''),
    ]
    actual_ranges = routers_utils.ParseIpRanges(self.messages, arg_ranges)
    self.assertEqual(expected_ranges, actual_ranges)
