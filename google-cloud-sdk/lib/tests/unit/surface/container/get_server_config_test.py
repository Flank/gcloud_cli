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

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.container import base


class GetServerConfigTestGA(base.TestBaseV1,
                            base.GATestBase,
                            base.GetServerConfigTestBase):
  """gcloud GA track using container v1 API."""

  def testZone(self):
    self.ExpectGetServerConfig(self.ZONE)
    self.Run(self.get_server_config_command_base +
             ' --zone={0}'.format(self.ZONE))
    self.AssertOutputContains('changelist 12345')
    self.AssertOutputContains('validMasterVersions:')

  def testMissingZone(self):
    with self.assertRaises(exceptions.MinimumArgumentException):
      self.Run(self.get_server_config_command_base)


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class GetServerConfigTestBetaV1API(base.BetaTestBase, GetServerConfigTestGA):
  """gcloud Beta track using container v1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(True)


# Mixin class must come in first to have the correct multi-inheritance behavior.
class GetServerConfigTestBetaV1Beta1API(base.TestBaseV1Beta1,
                                        GetServerConfigTestBetaV1API):
  """gcloud Beta track using container v1beta1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(False)

  def testRegion(self):
    self.ExpectGetServerConfig(self.REGION)
    self.Run(self.get_server_config_command_base +
             ' --region={0}'.format(self.REGION))
    self.AssertOutputEquals(
        'buildClientInfo: changelist 12345\n'
        'defaultClusterVersion: 1.2.3\n'
        'validMasterVersions:\n'
        '- 1.3.2\n')
    self.AssertErrEquals('Fetching server config for us-central1\n')


# Mixin class must come in first to have the correct multi-inheritance behavior.
class GetServerConfigTestAlphaV1API(base.AlphaTestBase,
                                    GetServerConfigTestBetaV1API):
  """gcloud Alpha track using container v1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(True)


# Mixin class must come in first to have the correct multi-inheritance behavior.
class GetServerConfigTestAlphaV1Alpha1API(base.TestBaseV1Alpha1,
                                          GetServerConfigTestAlphaV1API,
                                          GetServerConfigTestBetaV1Beta1API):
  """gcloud Alpha track using container v1alpha1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(False)


if __name__ == '__main__':
  test_case.main()
