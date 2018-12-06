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

"""Tests for 'get-server-config' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.container import base


class GetServerConfigTestGA(base.GATestBase,
                            base.GetServerConfigTestBase):
  """gcloud GA track using container v1 API."""

  def testZone(self):
    self.ExpectGetServerConfig(self.ZONE)
    self.Run(self.get_server_config_command_base +
             ' --zone={0}'.format(self.ZONE))
    self.AssertOutputContains('validMasterVersions:')

  def testRegion(self):
    self.ExpectGetServerConfig(self.REGION)
    self.Run(self.get_server_config_command_base +
             ' --region={0}'.format(self.REGION))
    self.AssertOutputContains('validMasterVersions:')

  def testMissingZoneAndRegion(self):
    with self.assertRaises(exceptions.MinimumArgumentException):
      self.Run(self.get_server_config_command_base)


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class GetServerConfigTestBeta(base.BetaTestBase, GetServerConfigTestGA):
  """gcloud Beta track using container v1beta1 API."""


# Mixin class must come in first to have the correct multi-inheritance behavior.
class GetServerConfigTestAlphaV1Alpha1API(
    base.AlphaTestBase, GetServerConfigTestBeta):
  """gcloud Alpha track using container v1alpha1 API."""


if __name__ == '__main__':
  test_case.main()
