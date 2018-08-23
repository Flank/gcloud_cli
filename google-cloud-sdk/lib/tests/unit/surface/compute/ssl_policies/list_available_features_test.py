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
"""Tests for the SSL policies list-available-features alpha command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import ssl_policies_test_base


class SslPolicyListAvailableFeaturesGATest(
    ssl_policies_test_base.SslPoliciesTestBase):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.GA)

  def testListAvailableFeatures(self):
    result_features = [
        'TLS_RSA_WITH_AES_128_CBC_SHA', 'TLS_RSA_WITH_AES_256_CBC_SHA',
        'TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA',
        'TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA'
    ]

    self.ExpectListAvailableFeaturesRequest(self.Project(), result_features)

    response = self.Run('compute ssl-policies list-available-features')
    self.assertEqual(response, result_features)
    self.AssertOutputEquals(
        textwrap.dedent("""\
        TLS_RSA_WITH_AES_128_CBC_SHA
        TLS_RSA_WITH_AES_256_CBC_SHA
        TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA
        TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA
        """))


class SslPolicyListAvailableFeaturesBetaTest(
    SslPolicyListAvailableFeaturesGATest):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.BETA)


class SslPolicyListAvailableFeaturesAlphaTest(
    SslPolicyListAvailableFeaturesBetaTest):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
