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
"""Tests for the matrix_creator_common module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import matrix_creator_common
from googlecloudsdk.core import config
from tests.lib import test_case
from tests.lib.surface.firebase.test import unit_base


class MatrixCreatorCommonTest(unit_base.TestMockClientTest):

  def SetUp(self):
    self.CreateMockedClients()

  def testBuildClientInfoAppendsUserProvidedClientDetails(self):
    client_info = matrix_creator_common.BuildClientInfo(self.testing_msgs, {
        'k1': 'v1',
        'k2': 'v2'
    }, '')
    self.assertIn(
        self.testing_msgs.ClientInfoDetail(key='k1', value='v1'),
        client_info.clientInfoDetails)
    self.assertIn(
        self.testing_msgs.ClientInfoDetail(key='k2', value='v2'),
        client_info.clientInfoDetails)

  def testBuildClientInfoOverwritesDefaultDetails(self):
    client_info = matrix_creator_common.BuildClientInfo(self.testing_msgs, {
        'Cloud SDK Version': 'a',
        'Release Track': 'a',
    }, 'release_track')
    self.assertIn(
        self.testing_msgs.ClientInfoDetail(
            key='Cloud SDK Version', value=config.CLOUD_SDK_VERSION),
        client_info.clientInfoDetails)
    self.assertIn(
        self.testing_msgs.ClientInfoDetail(
            key='Release Track', value='release_track'),
        client_info.clientInfoDetails)


if __name__ == '__main__':
  test_case.main()
