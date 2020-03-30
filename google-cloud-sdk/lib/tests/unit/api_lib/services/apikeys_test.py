# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Tests for api keys module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import apikeys
from tests.lib.surface.services import unit_test_base


class ApiKeysTest(unit_test_base.ApiKeysUnitTestBase):
  """Unit tests for api_keys module."""

  def testListKeys(self):
    """Test ListKeys returns keys when successful."""
    want = [
        self.services_messages.V2alpha1ApiKey(
            createTime='2019-01-12T01:13:41.635Z',
            displayName='API key 1',
            name='projects/103621867718/keys/7f1ce96e-7fb5-4d13-afc0-5b9d3bd5be14',
            restrictions=self.services_messages.V2alpha1Restrictions(
                androidKeyRestrictions=self.services_messages
                .V2alpha1AndroidKeyRestrictions(allowedApplications=[
                    self.services_messages.V2alpha1AndroidApplication(
                        packageName='test app', sha1Fingerprint='fingerprint')
                ])),
            state=self.services_messages.V2alpha1ApiKey.StateValueValuesEnum
            .ACTIVE,
            updateTime='2019-01-12T01:13:41.743154Z')
    ]
    self.ExpectListKeysCall(want)

    got = apikeys.ListKeys(self.DEFAULT_PROJECT)
    self.assertEqual([v for v in got], want)
