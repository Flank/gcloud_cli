# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Unit tests for Dataproc Metastore parsers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import utils as compute_api_lib
from googlecloudsdk.command_lib.metastore import parsers
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base

_COMPUTE_NETWORK_PREFIX = 'https://www.googleapis.com/compute/{}/'.format(
    compute_api_lib.COMPUTE_GA_API_VERSION)
_SECRET_MANAGER_SECRET_VERSION_PREFIX = 'https://secretmanager.googleapis.com/v1/'


class ParseNetworkTest(sdk_test_base.SdkBase):

  def SetUp(self):
    properties.VALUES.core.project.Set('my-project')

  def testParseNetworkId(self):
    expected_relative_link = 'projects/my-project/global/networks/test-network'
    actual_relative_link = parsers.ParseNetwork('test-network')
    self.assertEqual(actual_relative_link, expected_relative_link)

  def testParseNetworkRelative(self):
    expected_relative_link = 'projects/my-project/global/networks/test-network'
    actual_relative_link = parsers.ParseNetwork(expected_relative_link)
    self.assertEqual(actual_relative_link, expected_relative_link)

  def testParseNetworkUri(self):
    expected_relative_link = 'projects/my-project/global/networks/test-network'
    actual_relative_link = parsers.ParseNetwork(_COMPUTE_NETWORK_PREFIX +
                                                expected_relative_link)
    self.assertEqual(actual_relative_link, expected_relative_link)


class ParseSecretManagerSecretVersionTest(sdk_test_base.SdkBase):

  def SetUp(self):
    properties.VALUES.core.project.Set('my-project')

  def testParseSecretManagerSecretVersionRelative(self):
    expected_relative_link = 'projects/my-project/secrets/test/versions/1'
    actual_relative_link = parsers.ParseSecretManagerSecretVersion(
        expected_relative_link)
    self.assertEqual(actual_relative_link, expected_relative_link)

  def testParseSecretManagerSecretVersionUri(self):
    expected_relative_link = 'projects/my-project/secrets/test/versions/1'
    actual_relative_link = parsers.ParseSecretManagerSecretVersion(
        _SECRET_MANAGER_SECRET_VERSION_PREFIX + expected_relative_link)
    self.assertEqual(actual_relative_link, expected_relative_link)
