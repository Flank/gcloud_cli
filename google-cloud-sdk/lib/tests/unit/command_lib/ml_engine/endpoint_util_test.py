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
# Lint as: python3
"""Tests for the ML Engine endpoint utils."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.ml_engine import endpoint_util as util
from googlecloudsdk.core import properties
from tests.lib import test_case

BASE_URL = 'https://ml.googleapis.com/'
REGION = 'us-central1'


class EndpointUtilTest(test_case.TestCase):

  def testDeriveRegionalMlEndpoint(self):
    regional_endpoint = util.DeriveMLRegionalEndpoint(BASE_URL, REGION)
    self.assertEqual(regional_endpoint,
                     'https://us-central1-ml.googleapis.com/')

  def testConnectToRegion(self):
    existing_override = properties.VALUES.api_endpoint_overrides.ml.Get()
    with util.MlEndpointOverrides('us-central1'):
      self.assertEqual(properties.VALUES.api_endpoint_overrides.ml.Get(),
                       'https://us-central1-ml.googleapis.com/')
    self.assertEqual(properties.VALUES.api_endpoint_overrides.ml.Get(),
                     existing_override)

  def testGetRegionalMlEndpoint(self):
    regional_endpoint = util.GetRegionalMlEndpoint(REGION)
    self.assertEqual(regional_endpoint,
                     'https://us-central1-ml.googleapis.com/')


if __name__ == '__main__':
  test_case.main()
